import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '../context/AuthContext';

const API = `${window.location.origin}/lab-notebook`;

// ── helpers ───────────────────────────────────────────────────────────────────

function tokenHeaders(token) {
  return { Authorization: `Token ${token}` };
}

function jsonHeaders(token) {
  return { Authorization: `Token ${token}`, 'Content-Type': 'application/json' };
}

function fmtDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function stripHtml(html) {
  const d = document.createElement('div');
  d.innerHTML = html;
  return d.innerText || d.textContent || '';
}

async function triggerDownload(url, filename, token) {
  const res = await fetch(url, { headers: tokenHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || 'Download failed');
  }
  const blob = await res.blob();
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

// ── RecordingPanel ────────────────────────────────────────────────────────────

const MIN_SECONDS = 2;  // must record at least this long before Stop is enabled

function RecordingPanel({ token, onTranscribed }) {
  const [phase, setPhase]     = useState('idle');  // idle | recording | processing
  const [seconds, setSeconds] = useState(0);
  const [level, setLevel]     = useState(0);       // 0–100, live mic volume
  const [error, setError]     = useState('');

  const mediaRef    = useRef(null);
  const chunksRef   = useRef([]);
  const timerRef    = useRef(null);
  const analyserRef = useRef(null);
  const rafRef      = useRef(null);

  // Tear down the AnalyserNode animation loop
  const stopLevelMeter = () => {
    cancelAnimationFrame(rafRef.current);
    setLevel(0);
  };

  const startRecording = async () => {
    setError('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      chunksRef.current = [];

      // ── Live level meter via Web Audio AnalyserNode ──
      const ctx      = new (window.AudioContext || window.webkitAudioContext)();
      const source   = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      const buf = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteFrequencyData(buf);
        const avg = buf.reduce((a, b) => a + b, 0) / buf.length;
        setLevel(Math.min(100, Math.round(avg * 2.5)));  // scale 0–100
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();

      // ── MediaRecorder ──
      const mimeType = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus', 'audio/mp4']
        .find(m => MediaRecorder.isTypeSupported(m)) || '';
      const rec = new MediaRecorder(stream, mimeType ? { mimeType } : {});
      rec.ondataavailable = e => { if (e.data.size > 0) chunksRef.current.push(e.data); };
      rec.onstop = () => { stream.getTracks().forEach(t => t.stop()); ctx.close(); };

      mediaRef.current = rec;
      rec.start(250);
      setPhase('recording');
      setSeconds(0);
      timerRef.current = setInterval(() => setSeconds(s => s + 1), 1000);
    } catch (e) {
      setError('Microphone access denied. Please allow microphone in browser settings.');
    }
  };

  const stopAndTranscribe = async () => {
    clearInterval(timerRef.current);
    stopLevelMeter();
    setPhase('processing');
    const rec = mediaRef.current;
    if (!rec) return;

    await new Promise(resolve => {
      rec.onstop = () => { rec.stream?.getTracks().forEach(t => t.stop()); resolve(); };
      rec.stop();
    });

    const blob = new Blob(chunksRef.current, { type: rec.mimeType || 'audio/webm' });
    const form = new FormData();
    form.append('audio', blob, 'recording.webm');

    try {
      const res = await fetch(`${API}/transcribe/`, {
        method: 'POST',
        headers: tokenHeaders(token),
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Transcription failed');
      if (data.text) {
        onTranscribed({ text: data.text, summary: data.summary || null });
      } else {
        setError('No speech detected. Speak clearly and at normal volume, then try again.');
      }
    } catch (e) {
      setError(e.message || 'Transcription failed');
    } finally {
      setPhase('idle');
    }
  };

  const fmt   = s => `${Math.floor(s / 60).toString().padStart(2, '0')}:${(s % 60).toString().padStart(2, '0')}`;
  const canStop = seconds >= MIN_SECONDS;

  // Level bar colour: grey → green → amber → red
  const levelColor = level < 20 ? '#ccc' : level < 60 ? '#66bb6a' : level < 85 ? '#ffa726' : '#e53935';

  return (
    <div style={{
      background: '#fff', borderRadius: 14, border: '1px solid #e8e7e0',
      padding: '22px 32px', marginBottom: 20,
      display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap',
    }}>
      {/* Mic icon */}
      <div style={{
        width: 52, height: 52, borderRadius: '50%', flexShrink: 0,
        background: phase === 'recording' ? '#fff0f0' : '#f5f4ee',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        transition: 'background 0.3s',
        boxShadow: phase === 'recording' ? '0 0 0 6px rgba(229,57,53,0.12)' : 'none',
        animation: phase === 'recording' ? 'ring-pulse 1.5s ease-in-out infinite' : 'none',
      }}>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
          <rect x="9" y="2" width="6" height="11" rx="3"
            fill={phase === 'recording' ? '#e53935' : '#888'}/>
          <path d="M5 10a7 7 0 0 0 14 0" stroke={phase === 'recording' ? '#e53935' : '#888'}
            strokeWidth="2" strokeLinecap="round"/>
          <line x1="12" y1="19" x2="12" y2="22" stroke={phase === 'recording' ? '#e53935' : '#888'}
            strokeWidth="2" strokeLinecap="round"/>
          <line x1="8" y1="22" x2="16" y2="22" stroke={phase === 'recording' ? '#e53935' : '#888'}
            strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </div>

      {/* Label + level bar + status */}
      <div style={{ flex: 1, minWidth: 200 }}>
        <div style={{ fontWeight: 500, fontSize: '0.95em', color: '#1e1e1e' }}>
          {phase === 'idle'       && 'Voice Recording'}
          {phase === 'recording'  && <span style={{ color: '#e53935' }}>Recording… {fmt(seconds)}</span>}
          {phase === 'processing' && 'Transcribing & summarising…'}
        </div>

        {/* Live level bar — only visible while recording */}
        {phase === 'recording' && (
          <div style={{ marginTop: 8, marginBottom: 2 }}>
            <div style={{
              height: 4, borderRadius: 2, background: '#f0efe8',
              overflow: 'hidden', width: '100%', maxWidth: 260,
            }}>
              <div style={{
                height: '100%', borderRadius: 2,
                background: levelColor,
                width: `${level}%`,
                transition: 'width 0.08s ease, background 0.2s',
              }} />
            </div>
            <div style={{ fontSize: '0.72em', color: level < 10 ? '#e57373' : '#aaa', marginTop: 3 }}>
              {level < 10
                ? 'Mic level very low — speak louder or check your microphone'
                : 'Speak clearly. Click Stop & Transcribe when finished.'}
            </div>
          </div>
        )}

        {phase !== 'recording' && (
          <div style={{ fontSize: '0.8em', color: '#aaa', marginTop: 3 }}>
            {phase === 'idle'       && 'Click Record, speak your notes, then stop. Minimum 2 seconds.'}
            {phase === 'processing' && 'Please wait — Whisper transcribes, then the model builds a summary.'}
          </div>
        )}

        {error && (
          <div style={{ fontSize: '0.8em', color: '#e53935', marginTop: 6 }}>{error}</div>
        )}
      </div>

      {/* Buttons */}
      {phase === 'idle' && (
        <button onClick={startRecording} style={btnStyle('#e53935', '#fff')}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10"/>
          </svg>
          Record
        </button>
      )}
      {phase === 'recording' && (
        <button
          onClick={stopAndTranscribe}
          disabled={!canStop}
          title={!canStop ? `Keep recording (${MIN_SECONDS - seconds}s more)` : ''}
          style={{
            ...btnStyle('#1e1e1e', '#fff'),
            opacity: canStop ? 1 : 0.45,
            cursor: canStop ? 'pointer' : 'not-allowed',
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <rect x="4" y="4" width="16" height="16" rx="2"/>
          </svg>
          {canStop ? 'Stop & Transcribe' : `Wait… ${MIN_SECONDS - seconds}s`}
        </button>
      )}
      {phase === 'processing' && (
        <div style={{ fontSize: '0.82em', color: '#888', fontStyle: 'italic' }}>Processing…</div>
      )}
    </div>
  );
}

function btnStyle(bg, fg) {
  return {
    display: 'flex', alignItems: 'center', gap: 8,
    padding: '9px 20px', border: 'none', borderRadius: 8,
    background: bg, color: fg, cursor: 'pointer',
    fontSize: '0.88em', fontWeight: 600,
    whiteSpace: 'nowrap', flexShrink: 0,
    boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
    transition: 'opacity 0.15s',
  };
}

// ── ToolbarBtn ────────────────────────────────────────────────────────────────

function ToolbarBtn({ children, title, onClick }) {
  return (
    <button
      title={title}
      onMouseDown={e => { e.preventDefault(); onClick(); }}
      style={{
        width: 30, height: 30, border: '1px solid #d4d3cc', borderRadius: 6,
        background: '#fff', cursor: 'pointer', fontSize: '0.82em', fontWeight: 700,
        color: '#444', display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      {children}
    </button>
  );
}

// ── ExportBtn ─────────────────────────────────────────────────────────────────

function ExportBtn({ label, loading, onClick, color }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        padding: '6px 14px', fontSize: '0.8em', fontWeight: 500,
        border: `1px solid ${color || '#d4d3cc'}`, borderRadius: 6,
        background: loading ? '#f5f5f5' : '#fff',
        color: loading ? '#aaa' : (color || '#555'),
        cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      {loading ? '…' : label}
    </button>
  );
}

// ── AuditPanel ────────────────────────────────────────────────────────────────

function AuditPanel({ noteId, token }) {
  const [open, setOpen]     = useState(false);
  const [logs, setLogs]     = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // reset when note changes
    setOpen(false);
    setLogs([]);
  }, [noteId]);

  const load = async () => {
    if (logs.length > 0) { setOpen(o => !o); return; }
    setLoading(true);
    try {
      const res = await fetch(`${API}/notes/${noteId}/history/`, {
        headers: { Authorization: `Token ${token}` },
      });
      const data = await res.json();
      setLogs(data);
      setOpen(true);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const actionColor = { created: '#81c784', edited: '#7b9ea6' };
  const actionLabel = { created: 'Created', edited: 'Edited' };

  return (
    <div style={{ borderTop: '1px solid #f5f4ee' }}>
      <button
        onClick={load}
        style={{
          width: '100%', padding: '7px 22px', border: 'none', background: 'transparent',
          cursor: 'pointer', textAlign: 'left', fontSize: '0.72em', color: '#bbb',
          display: 'flex', alignItems: 'center', gap: 6,
        }}
      >
        <svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
          <circle cx="8" cy="8" r="6.5"/>
          <polyline points="8,4 8,8 11,10"/>
        </svg>
        {loading ? 'Loading history…' : (open ? 'Hide edit history' : 'Show edit history')}
      </button>

      {open && (
        <div style={{ padding: '0 22px 12px', maxHeight: 160, overflowY: 'auto' }}>
          {logs.length === 0 ? (
            <p style={{ margin: 0, fontSize: '0.75em', color: '#ccc' }}>No history yet.</p>
          ) : logs.map((entry, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '4px 0', borderBottom: i < logs.length - 1 ? '1px solid #f5f4ee' : 'none',
            }}>
              <span style={{
                fontSize: '0.68em', fontWeight: 600, letterSpacing: '0.4px',
                color: '#fff', background: actionColor[entry.action] || '#ccc',
                padding: '1px 6px', borderRadius: 4, textTransform: 'uppercase', flexShrink: 0,
              }}>
                {actionLabel[entry.action] || entry.action}
              </span>
              <span style={{ fontSize: '0.75em', color: '#888', fontWeight: 500 }}>{entry.user}</span>
              <span style={{ fontSize: '0.72em', color: '#bbb', marginLeft: 'auto' }}>{entry.timestamp}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function LabNotebook({ onBack }) {
  const { token } = useAuth();

  const [notes, setNotes]             = useState([]);
  const [selectedId, setSelectedId]   = useState(null);
  const [title, setTitle]             = useState('');
  const [saveStatus, setSaveStatus]   = useState('');
  const [loading, setLoading]         = useState(true);
  const [exporting, setExporting]     = useState('');  // '' | 'pdf' | 'docx'

  const editorRef    = useRef(null);
  const saveTimerRef = useRef(null);

  // ── fetch ──────────────────────────────────────────────────────────────────

  const fetchNotes = useCallback(async () => {
    try {
      const res = await fetch(`${API}/notes/`, { headers: jsonHeaders(token) });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        console.error('fetchNotes failed', res.status, body);
        return [];
      }
      const data = await res.json();
      setNotes(data);
      return data;
    } catch (e) {
      console.error('fetchNotes error', e);
      return [];
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchNotes(); }, [fetchNotes]);

  // ── load note into editor ──────────────────────────────────────────────────

  const loadNote = useCallback((note) => {
    setSelectedId(note.id);
    setTitle(note.title);
    if (editorRef.current) editorRef.current.innerHTML = note.content || '';
    setSaveStatus('');
  }, []);

  // ── auto-save ──────────────────────────────────────────────────────────────

  const scheduleSave = useCallback((overrideId, overrideTitle) => {
    const id = overrideId ?? selectedId;
    if (!id) return;
    clearTimeout(saveTimerRef.current);
    setSaveStatus('saving');
    saveTimerRef.current = setTimeout(async () => {
      try {
        const content = editorRef.current ? editorRef.current.innerHTML : '';
        const t = overrideTitle ?? title;
        const res = await fetch(`${API}/notes/${id}/`, {
          method: 'PUT',
          headers: jsonHeaders(token),
          body: JSON.stringify({ title: t, content }),
        });
        if (!res.ok) throw new Error();
        const updated = await res.json();
        setNotes(prev => prev.map(n => n.id === id ? updated : n));
        setSaveStatus('saved');
      } catch {
        setSaveStatus('error');
      }
    }, 800);
  }, [selectedId, title, token]);

  // ── create note ────────────────────────────────────────────────────────────

  const createNote = useCallback(async (initialTitle = 'Untitled Note', initialContent = '') => {
    const res = await fetch(`${API}/notes/`, {
      method: 'POST',
      headers: jsonHeaders(token),
      body: JSON.stringify({ title: initialTitle, content: initialContent }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || body.error || `Server error ${res.status}`);
    }
    return res.json();
  }, [token]);

  const handleNewNote = async () => {
    try {
      const note = await createNote();
      setNotes(prev => [note, ...prev]);
      loadNote(note);
    } catch (e) {
      alert(`Could not create note: ${e.message}`);
    }
  };

  // ── transcription callback ─────────────────────────────────────────────────

  const handleTranscribed = useCallback(async ({ text, summary }) => {
    let noteId = selectedId;
    let noteTitle = title;

    // Auto-create a note if none is open
    if (!noteId) {
      try {
        const ts = new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        const note = await createNote(`Recording – ${ts}`, '');
        setNotes(prev => [note, ...prev]);
        loadNote(note);
        noteId = note.id;
        noteTitle = note.title;
      } catch (e) {
        alert(`Failed to create note: ${e.message}`);
        return;
      }
    }

    // Build the HTML block to insert
    if (editorRef.current) {
      editorRef.current.focus();
      const existing = editorRef.current.innerHTML.trim();
      const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

      let block = `<p>${escaped}</p>`;

      if (summary) {
        block += [
          `<hr style="border:none;border-top:1px solid #e8e7e0;margin:20px 0">`,
          `<p><strong style="font-size:0.82em;letter-spacing:0.6px;text-transform:uppercase;color:#7b9ea6">Summary</strong></p>`,
          summary,
        ].join('');
      }

      editorRef.current.innerHTML = existing ? `${existing}${block}` : block;
    }

    scheduleSave(noteId, noteTitle);
  }, [selectedId, title, createNote, loadNote, scheduleSave]);

  // ── delete ─────────────────────────────────────────────────────────────────

  const handleDelete = async () => {
    if (!selectedId || !window.confirm('Delete this note? This cannot be undone.')) return;
    await fetch(`${API}/notes/${selectedId}/`, { method: 'DELETE', headers: jsonHeaders(token) });
    const remaining = notes.filter(n => n.id !== selectedId);
    setNotes(remaining);
    if (remaining.length > 0) { loadNote(remaining[0]); }
    else { setSelectedId(null); setTitle(''); if (editorRef.current) editorRef.current.innerHTML = ''; }
  };

  // ── formatting ─────────────────────────────────────────────────────────────

  const fmt = (cmd) => { editorRef.current?.focus(); document.execCommand(cmd, false, null); scheduleSave(); };

  // ── exports ────────────────────────────────────────────────────────────────

  const saveNow = async () => {
    if (!selectedId) return;
    clearTimeout(saveTimerRef.current);
    const content = editorRef.current ? editorRef.current.innerHTML : '';
    await fetch(`${API}/notes/${selectedId}/`, {
      method: 'PUT', headers: jsonHeaders(token),
      body: JSON.stringify({ title, content }),
    }).catch(() => {});
  };

  const handlePdf = async () => {
    await saveNow();
    setExporting('pdf');
    try {
      await triggerDownload(`${API}/notes/${selectedId}/pdf/`, `lab_note_${selectedId}.pdf`, token);
    } catch (e) { alert(e.message); }
    finally { setExporting(''); }
  };

  const handleDocx = async () => {
    await saveNow();
    setExporting('docx');
    try {
      await triggerDownload(`${API}/notes/${selectedId}/docx/`, `lab_note_${selectedId}.docx`, token);
    } catch (e) { alert(e.message); }
    finally { setExporting(''); }
  };

  const handleTxt = () => {
    if (!editorRef.current || !selectedNote) return;
    const fmt8 = iso => new Date(iso).toLocaleString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
    });
    const meta = [
      `Note ID:       #${selectedNote.id}`,
      `Author:        ${selectedNote.created_by_username}`,
      `Created:       ${fmt8(selectedNote.created_at)} UTC`,
      `Last modified: ${fmt8(selectedNote.updated_at)} UTC`,
    ].join('\n');
    const text = [
      title,
      '─'.repeat(60),
      meta,
      '─'.repeat(60),
      '',
      stripHtml(editorRef.current.innerHTML),
    ].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: 'text/plain' }));
    a.download = `lab_note_${selectedId || 'export'}.txt`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  // ── render ─────────────────────────────────────────────────────────────────

  const selectedNote = notes.find(n => n.id === selectedId);

  return (
    <>
      <style>{`
        @keyframes ring-pulse {
          0%,100% { box-shadow: 0 0 0 0 rgba(229,57,53,0.25); }
          50%      { box-shadow: 0 0 0 10px rgba(229,57,53,0); }
        }
        .nb-editor:empty:before {
          content: attr(data-placeholder);
          color: #ccc;
          pointer-events: none;
          position: absolute;
        }
        .nb-editor { position: relative; }
        .nb-editor:focus { outline: none; }
        .nb-note-item { transition: background 0.1s; }
        .nb-note-item:hover { background: #eae9e2 !important; }
      `}</style>

      <div style={{
        display: 'flex', flexDirection: 'column', minHeight: '100vh',
        padding: '40px 48px', background: '#f0efe8',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        boxSizing: 'border-box',
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 }}>
          <button onClick={onBack} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#888', fontSize: '0.85em', padding: '4px 0',
            display: 'flex', alignItems: 'center', gap: 4,
          }}>← Back</button>
          <h2 style={{ margin: 0, fontSize: '1.6em', fontWeight: 400, color: '#1e1e1e', letterSpacing: '-0.3px' }}>
            Lab Notebook
          </h2>
        </div>

        {/* Recording panel (always visible) */}
        <RecordingPanel token={token} onTranscribed={handleTranscribed} />

        {/* Two-pane layout */}
        <div style={{ display: 'flex', gap: 16, flex: 1, minHeight: 0 }}>

          {/* ── Left: note list ── */}
          <div style={{
            width: 220, flexShrink: 0, background: '#fff',
            borderRadius: 14, border: '1px solid #e8e7e0',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
          }}>
            <div style={{ padding: '12px 14px', borderBottom: '1px solid #f0efe8' }}>
              <button onClick={handleNewNote} style={{
                width: '100%', padding: '7px 0',
                border: '1px dashed #c8c7c0', borderRadius: 8,
                background: 'transparent', cursor: 'pointer',
                color: '#888', fontSize: '0.82em', fontWeight: 500,
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 5,
              }}>
                <svg width="11" height="11" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="6" y1="1" x2="6" y2="11"/><line x1="1" y1="6" x2="11" y2="6"/>
                </svg>
                New Note
              </button>
            </div>

            <div style={{ overflowY: 'auto', flex: 1 }}>
              {loading && <p style={{ padding: '16px', color: '#bbb', fontSize: '0.8em', margin: 0 }}>Loading…</p>}
              {!loading && notes.length === 0 && (
                <p style={{ padding: '16px', color: '#bbb', fontSize: '0.8em', margin: 0 }}>
                  No notes yet. Record or click New Note.
                </p>
              )}
              {notes.map(note => (
                <div
                  key={note.id}
                  className="nb-note-item"
                  onClick={() => loadNote(note)}
                  style={{
                    padding: '11px 14px', cursor: 'pointer',
                    borderBottom: '1px solid #f5f4ee',
                    background: note.id === selectedId ? '#e0dfd8' : 'transparent',
                  }}
                >
                  <div style={{
                    fontSize: '0.83em', fontWeight: 500, color: '#1e1e1e',
                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  }}>
                    {note.title || 'Untitled Note'}
                  </div>
                  <div style={{ fontSize: '0.72em', color: '#aaa', marginTop: 2 }}>
                    {fmtDate(note.updated_at)}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Right: editor ── */}
          <div style={{
            flex: 1, background: '#fff', borderRadius: 14,
            border: '1px solid #e8e7e0',
            display: 'flex', flexDirection: 'column', overflow: 'hidden',
          }}>
            {!selectedId ? (
              <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 10, color: '#ccc',
              }}>
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="#ddd" strokeWidth="1.5">
                  <rect x="6" y="4" width="28" height="32" rx="3"/>
                  <line x1="12" y1="14" x2="28" y2="14"/>
                  <line x1="12" y1="20" x2="28" y2="20"/>
                  <line x1="12" y1="26" x2="22" y2="26"/>
                </svg>
                <p style={{ margin: 0, fontSize: '0.88em' }}>
                  Select a note, create one, or record — a note will be created automatically.
                </p>
              </div>
            ) : (
              <>
                {/* Title */}
                <div style={{ padding: '18px 22px 0' }}>
                  <input
                    value={title}
                    onChange={e => { setTitle(e.target.value); scheduleSave(null, e.target.value); }}
                    placeholder="Note title…"
                    style={{
                      width: '100%', border: 'none', outline: 'none',
                      fontSize: '1.25em', fontWeight: 500, color: '#1e1e1e',
                      background: 'transparent', fontFamily: 'inherit', boxSizing: 'border-box',
                    }}
                  />
                </div>

                {/* Compliance metadata strip — read-only, always visible */}
                {selectedNote && (
                  <div style={{
                    padding: '6px 22px 8px',
                    borderBottom: '1px solid #f5f4ee',
                    display: 'flex', flexWrap: 'wrap', gap: '4px 20px',
                    background: '#fafaf8',
                  }}>
                    {[
                      { label: 'Note', value: `#${selectedNote.id}` },
                      { label: 'Author', value: selectedNote.created_by_username },
                      { label: 'Created', value: new Date(selectedNote.created_at).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) },
                      { label: 'Last saved', value: new Date(selectedNote.updated_at).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' }) },
                    ].map(({ label, value }) => (
                      <span key={label} style={{ fontSize: '0.72em', color: '#aaa', userSelect: 'none' }}>
                        <span style={{ color: '#bbb', fontWeight: 500 }}>{label}:</span> {value}
                      </span>
                    ))}
                  </div>
                )}

                {/* Toolbar */}
                <div style={{
                  display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
                  padding: '10px 22px', borderBottom: '1px solid #f0efe8',
                }}>
                  <ToolbarBtn title="Bold (Ctrl+B)" onClick={() => fmt('bold')}><b>B</b></ToolbarBtn>
                  <ToolbarBtn title="Italic (Ctrl+I)" onClick={() => fmt('italic')}><i>I</i></ToolbarBtn>
                  <ToolbarBtn title="Underline (Ctrl+U)" onClick={() => fmt('underline')}><u>U</u></ToolbarBtn>

                  <div style={{ width: 1, height: 20, background: '#e4e3dc', margin: '0 2px' }} />

                  {saveStatus === 'saving' && <span style={{ fontSize: '0.76em', color: '#aaa' }}>Saving…</span>}
                  {saveStatus === 'saved'  && <span style={{ fontSize: '0.76em', color: '#81c784' }}>Saved ✓</span>}
                  {saveStatus === 'error'  && <span style={{ fontSize: '0.76em', color: '#e57373' }}>Save failed</span>}

                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
                    <ExportBtn label="TXT"  onClick={handleTxt} />
                    <ExportBtn label="DOCX" loading={exporting === 'docx'} onClick={handleDocx} color="#1565c0" />
                    <ExportBtn label="PDF"  loading={exporting === 'pdf'}  onClick={handlePdf}  color="#b71c1c" />
                    <button onClick={handleDelete} style={{
                      padding: '6px 10px', fontSize: '0.78em',
                      border: '1px solid #f5c6c6', borderRadius: 6,
                      background: '#fff', color: '#e57373', cursor: 'pointer',
                    }}>Delete</button>
                  </div>
                </div>

                {/* Editor */}
                <div
                  ref={editorRef}
                  contentEditable
                  suppressContentEditableWarning
                  className="nb-editor"
                  data-placeholder="Start typing, or record your voice above…"
                  onInput={() => scheduleSave()}
                  style={{
                    flex: 1, overflowY: 'auto', padding: '18px 22px',
                    fontSize: '0.95em', lineHeight: 1.75, color: '#1e1e1e', minHeight: 200,
                  }}
                />

                {/* Audit history panel */}
                <AuditPanel noteId={selectedId} token={token} />
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
