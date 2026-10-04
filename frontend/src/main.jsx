import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API = import.meta.env.VITE_API_BASE || ''

function Stat({label, value, sub}) {
  return <div className="stat"><div className="statLabel">{label}</div><div className="statValue">{value}</div>{sub && <div className="statSub">{sub}</div>}</div>
}

function ScoreRing({score}) {
  const r = 52, c = 2 * Math.PI * r, dash = c * Math.max(0, Math.min(100, score)) / 100
  return <div className="ringWrap">
    <svg viewBox="0 0 128 128" className="ring">
      <circle cx="64" cy="64" r={r} className="ringBg" />
      <circle cx="64" cy="64" r={r} className="ringFg" strokeDasharray={`${dash} ${c-dash}`} />
    </svg>
    <div className="ringText"><strong>{score}</strong><span>EIS</span></div>
  </div>
}

function Graph({nodes, edges}) {
  const layout = useMemo(() => {
    const roots = nodes.filter(n => n.root)
    const others = nodes.filter(n => !n.root)
    const pos = {}
    roots.forEach((n,i)=> pos[n.id] = {x: 160, y: 90 + i*120})
    others.forEach((n,i)=> pos[n.id] = {x: 510 + (i%2)*230, y: 70 + Math.floor(i/2)*105})
    return pos
  }, [nodes])
  const height = Math.max(420, 150 + Math.ceil(Math.max(1,nodes.length-1)/2)*110)
  return <div className="graphShell">
    <svg viewBox={`0 0 980 ${height}`} className="graphSvg" role="img" aria-label="Source lineage graph">
      <defs>
        <marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" /></marker>
      </defs>
      {edges.map((e,i)=> {
        const a=layout[e.source], b=layout[e.target]; if(!a||!b) return null
        return <g key={i}><line x1={a.x} y1={a.y} x2={b.x} y2={b.y} className={`edge ${e.kind}`} markerEnd="url(#arrow)" /><text x={(a.x+b.x)/2} y={(a.y+b.y)/2-6} className="edgeLabel">{e.kind}</text></g>
      })}
      {nodes.map(n=> { const p=layout[n.id]; return <g key={n.id} transform={`translate(${p.x},${p.y})`}>
        <circle r="32" className={n.root ? 'node rootNode' : 'node'} />
        <text y="4" textAnchor="middle" className="nodeMark">{n.root ? 'ROOT' : 'SRC'}</text>
        <text x="46" y="-7" className="nodeTitle">{n.domain}</text>
        <text x="46" y="14" className="nodeMeta">cluster {n.cluster+1}</text>
      </g>})}
    </svg>
  </div>
}

function App(){
  const [claim,setClaim]=useState('')
  const [urls,setUrls]=useState('')
  const [result,setResult]=useState(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState('')
  const [tab,setTab]=useState('analyze')

  const run = async (demo=false) => {
    setLoading(true); setError(''); setResult(null)
    try {
      const res = demo
        ? await fetch(`${API}/api/demo`)
        : await fetch(`${API}/api/analyze`, {method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({claim, source_urls: urls.split(/\n|,/).map(s=>s.trim()).filter(Boolean), max_sources:12})})
      const data = await res.json()
      if(!res.ok) throw new Error(data.detail || 'Analysis failed')
      setResult(data); setTab('results')
    } catch(e){ setError(e.message || String(e)) }
    finally{ setLoading(false) }
  }

  return <>
    <header className="nav">
      <div className="brand"><div className="dnaLogo">S</div><div><b>SourceDNA</b><span>Evidence lineage for the AI web</span></div></div>
      <div className="navRight"><span className="beta">HACKATHON MVP</span><a href="https://github.com/" target="_blank">GitHub</a></div>
    </header>

    <main>
      <section className="hero">
        <div className="eyebrow">THE INTERNET COUNTS REPETITION AS EVIDENCE. WE DON'T.</div>
        <h1>Find the <em>source</em><br/>behind the sources.</h1>
        <p>Trace a claim through the web, collapse derivative reporting, detect synthetic consensus, and see how many genuinely independent evidence roots remain.</p>
        <div className="heroPills"><span>Source lineage</span><span>Claim drift</span><span>Evidence Independence Score</span><span>MCP-ready</span></div>
      </section>

      <section className="workbench">
        <div className="tabs">
          <button className={tab==='analyze'?'active':''} onClick={()=>setTab('analyze')}>Analyze claim</button>
          <button className={tab==='results'?'active':''} onClick={()=>result&&setTab('results')} disabled={!result}>Evidence graph</button>
          <button className="demoBtn" onClick={()=>run(true)} disabled={loading}>Run synthetic-consensus demo</button>
        </div>

        {tab==='analyze' && <div className="panel inputPanel">
          <div className="field">
            <label>CLAIM OR STATEMENT</label>
            <textarea value={claim} onChange={e=>setClaim(e.target.value)} placeholder="Example: Remote workers are 47% more productive." />
          </div>
          <div className="field">
            <label>SOURCE URLS <span>optional — one per line</span></label>
            <textarea className="urls" value={urls} onChange={e=>setUrls(e.target.value)} placeholder={'https://example.com/article-one\nhttps://example.org/report'} />
            <small>Leave blank to use live search when your backend has a TAVILY_API_KEY. Paste URLs to test without a search API.</small>
          </div>
          {error && <div className="error">{error}</div>}
          <div className="actions"><button className="primary" onClick={()=>run(false)} disabled={loading || claim.trim().length<5}>{loading?'Tracing evidence…':'Analyze evidence →'}</button></div>
        </div>}

        {tab==='results' && result && <div className="results">
          <div className="summaryCard">
            <ScoreRing score={result.metrics.evidence_independence_score}/>
            <div className="summaryCopy"><div className={`risk ${result.metrics.synthetic_consensus_risk}`}>{result.metrics.synthetic_consensus_risk.toUpperCase()} SYNTHETIC-CONSENSUS RISK</div><h2>{result.verdict}</h2><p>{result.explanation}</p><blockquote>“{result.claim}”</blockquote></div>
          </div>
          <div className="statsGrid">
            <Stat label="Cited URLs" value={result.metrics.cited_urls}/>
            <Stat label="Independent roots" value={result.metrics.independent_roots} sub="after lineage collapse"/>
            <Stat label="Derivative sources" value={result.metrics.derivative_sources}/>
            <Stat label="Unique domains" value={result.metrics.unique_domains}/>
            <Stat label="Claim drift" value={`${result.metrics.claim_drift_score}%`}/>
          </div>
          <div className="sectionHead"><div><span>GENEALOGY</span><h3>Source lineage graph</h3></div><p>Arrows point from dependent/derivative pages toward the evidence they rely on.</p></div>
          <Graph nodes={result.nodes} edges={result.edges}/>
          <div className="sourceList">
            {result.nodes.map(n=><a className={`sourceRow ${n.root?'rootRow':''}`} href={n.url} target="_blank" key={n.id}>
              <div className="sourceBadge">{n.root?'ROOT':'SRC'}</div><div className="sourceBody"><b>{n.title}</b><span>{n.domain}{n.published_at?` · ${n.published_at.slice(0,10)}`:''}</span>{n.claim_snippet&&<p>{n.claim_snippet}</p>}</div><div className="cluster">C{n.cluster+1}</div>
            </a>)}
          </div>
          {result.warnings?.length>0 && <div className="warnings"><b>Analysis notes</b>{result.warnings.map((w,i)=><p key={i}>{w}</p>)}</div>}
          <div className="method"><b>Important:</b> SourceDNA's EIS is an experimental measure of <strong>evidence independence</strong>. It does not label a claim true or false.</div>
        </div>}
      </section>

      <section className="how"><div><span className="eyebrow">HOW IT THINKS</span><h2>Eight citations can still be one source.</h2></div><div className="steps"><article><b>01</b><h3>Discover</h3><p>Find webpages supporting or discussing the claim.</p></article><article><b>02</b><h3>Compare</h3><p>Measure textual similarity, links, domains and publication timing.</p></article><article><b>03</b><h3>Collapse</h3><p>Group derivative reporting into shared evidence lineages.</p></article><article><b>04</b><h3>Score</h3><p>Report independent roots, claim drift and an experimental EIS.</p></article></div></section>
    </main>
    <footer><b>SourceDNA</b><span>Repetition is not evidence.</span><span>Built for the AI-native web.</span></footer>
  </>
}

createRoot(document.getElementById('root')).render(<App/>)
