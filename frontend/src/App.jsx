import { useEffect, useState } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { getDecks } from './api.js';
import { sampleDecks, sampleEvents, sampleMeta } from './sampleData.js';

const screens = [
  ['/', 'Dashboard'], ['/decks', 'Deck Browser'],
  ['/decks/preview', 'Deck Details'], ['/tournaments', 'Tournament & Matchup Statistics'],
];

function Panel({ title, note, children }) {
  return <section className="panel">
    <div className="panel-heading"><h2>{title}</h2>{note && <span>{note}</span>}</div>
    {children}
  </section>;
}

function Dashboard() {
  return <>
    <h1>Dashboard</h1>
    <p className="subtitle">Overview of recent tournament activity and the competitive metagame.</p>
    <p className="notice">Layout preview: all dashboard numbers below are sample data.</p>
    <div className="summary-grid">
      {[["Tournaments", '48', 'Recent tracked events'], ['Decklists', '1,284', 'From tournament entries'], ['Matches', '3,820', 'With recorded results']].map(([label, value, hint]) =>
        <section className="summary" key={label}><h2>{label}</h2><strong>{value}</strong><p>{hint}</p></section>,
      )}
    </div>
    <div className="two-columns">
      <Panel title="Most played deck archetypes" note="Sample meta share">
        <div className="meta-list">{sampleMeta.map(([name, percent]) =>
          <div className="meta-row" key={name}><span>{name}</span><div className="bar-track"><div style={{ width: `${percent * 4}%` }} /></div><strong>{percent}%</strong></div>,
        )}</div>
      </Panel>
      <Panel title="Recent tournaments" note={<Link to="/tournaments">View tournaments →</Link>}>
        <div className="table-scroll"><table><thead><tr><th>Tournament</th><th>Date</th><th>Players</th></tr></thead>
          <tbody>{sampleEvents.map(([name, date, players]) => <tr key={name}><td>{name}</td><td>{date}</td><td>{players}</td></tr>)}</tbody>
        </table></div>
      </Panel>
    </div>
  </>;
}

function DeckBrowser() {
  const [result, setResult] = useState({ items: [], total: 0 });
  const [format, setFormat] = useState('');
  const [query, setQuery] = useState('');
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    const timeout = setTimeout(() => controller.abort(), 8000);
    setLoading(true);
    setError('');
    getDecks({ format, offset, signal: controller.signal })
      .then(data => { if (active) setResult(data); })
      .catch(err => {
        if (!active) return;
        setError(err.name === 'AbortError' ? 'The deck API timed out.' : err.message);
        setResult({ items: sampleDecks.filter(deck => !format || deck.format === format), total: 5 });
      })
      .finally(() => { if (active) setLoading(false); clearTimeout(timeout); });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
  }, [format, offset, attempt]);

  const decks = result.items.filter(deck =>
    [deck.name, deck.archetype, deck.player].some(value => value?.toLowerCase().includes(query.toLowerCase())),
  );

  return <>
    <h1>Browse Decklists</h1>
    <p className="subtitle">Find decks used by competitors in recent tournaments.</p>
    <div className="filters">
      <label>Search this page<input type="search" placeholder="Deck, archetype, or player…" value={query} onChange={event => setQuery(event.target.value)} /></label>
      <label>Format<select value={format} onChange={event => { setFormat(event.target.value); setOffset(0); }}>
        <option value="">All formats</option>{['Standard', 'Modern', 'Pioneer', 'Legacy', 'Vintage', 'Pauper', 'Commander'].map(name => <option key={name}>{name}</option>)}
      </select></label>
      <button onClick={() => setAttempt(value => value + 1)} disabled={loading}>Reload API</button>
    </div>
    {loading ? <p className="notice" role="status">Loading decks from the backend…</p> : <>
      <p className="notice" role="status">{error
        ? `${error} Showing sample decks, not database records. Start the backend and database, then reload.`
        : 'Connected to the backend API. Player, event, and result fields are not part of the list endpoint yet.'}</p>
      <Panel title="Tournament decklists" note={error ? `${decks.length} sample results` : `${decks.length} shown · ${result.total} total`}>
        <div className="table-scroll"><table>
          <thead><tr><th>Deck / archetype</th><th>Player</th><th>Event</th><th>Record</th><th>Finish</th><th><span className="sr-only">Details</span></th></tr></thead>
          <tbody>{decks.map(deck => <tr key={deck.id}>
            <td><strong>{deck.name}</strong><small>{deck.format} · {deck.archetype || 'Unclassified'}</small></td>
            <td>{deck.player || '—'}</td><td>{deck.event || '—'}</td><td>{deck.record || '—'}</td><td>{deck.finish || '—'}</td>
            <td><Link to={`/decks/${deck.id}`} state={{ deck, sample: Boolean(error) }}>View →</Link></td>
          </tr>)}</tbody>
        </table></div>
        {decks.length === 0 && <p className="empty">No decks found. Try another search or format.</p>}
      </Panel>
      {!error && <div className="pagination">
        <button disabled={offset === 0} onClick={() => setOffset(value => Math.max(0, value - 20))}>Previous</button>
        <span>Page {Math.floor(offset / 20) + 1}</span>
        <button disabled={offset + 20 >= result.total} onClick={() => setOffset(value => value + 20)}>Next</button>
      </div>}
    </>}
  </>;
}

function DeckDetails() {
  const { state } = useLocation();
  return <>
    <Link to="/decks">← Back to deck browser</Link>
    <h1>{state?.deck?.name || 'Deck Details'}</h1>
    <p className="subtitle">{state?.deck ? `${state.deck.format} · ${state.deck.archetype || 'Unclassified'}${state.sample ? ' · Sample deck' : ''}` : 'Select a deck in the browser to preview its name and format.'}</p>
    <Panel title="Deck details — coming later"><p className="empty">Main deck, sideboard, and tournament appearances will go here. This screen is a navigation placeholder for now.</p></Panel>
  </>;
}

function Statistics() {
  return <>
    <h1>Tournament &amp; Matchup Statistics</h1>
    <p className="subtitle">Explore tournament standings and how deck archetypes perform against each other.</p>
    <div className="two-columns">
      <Panel title="Final standings"><p className="empty">Tournament selection and standings are planned for a later step.</p></Panel>
      <Panel title="Matchup win rates"><p className="empty">Match counts and win-rate calculations are planned for a later step.</p></Panel>
    </div>
  </>;
}

export default function App() {
  const { pathname } = useLocation();
  const title = pathname.startsWith('/decks/') ? 'Deck Details' : screens.find(([path]) => path === pathname)?.[1] || 'Page not found';
  useEffect(() => { document.title = `${title} | MTG Tracker`; }, [title]);
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <aside>
      <div className="brand"><span className="brand-mark">M</span><div><strong>MTG Tracker</strong><small>Tournament analytics</small></div></div>
      <p className="nav-label">Navigation</p>
      <nav aria-label="Main navigation">{screens.map(([path, name]) => <Link key={path} to={path} className={title === name ? 'active' : ''} aria-current={title === name ? 'page' : undefined}>{name}</Link>)}</nav>
      <p className="sidebar-note">Frontend implementation<br />Work in progress</p>
    </aside>
    <div className="workspace">
      <header><span>Magic: The Gathering / <strong>{title}</strong></span><span className="badge">Implementation preview</span></header>
      <main id="main-content" key={pathname} tabIndex={-1}><Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/decks" element={<DeckBrowser />} />
        <Route path="/decks/:deckId" element={<DeckDetails />} />
        <Route path="/tournaments" element={<Statistics />} />
        <Route path="*" element={<><h1>Page not found</h1><Link to="/">Back to Dashboard</Link></>} />
      </Routes></main>
    </div>
  </div>;
}
