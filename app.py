"""
Ratan Tata Knowledge Graph — one-screen Streamlit app.

  +--------------------------------------------+----------------------+
  |                                            |  💬 Chat window      |
  |   (layout: 💬 Chat | 🕸️ Graph | 🔎 Query  — three full-height columns)   |
  |                                            +----------------------+
  |                                            |                      |
  +--------------------------------------------+----------------------+

Run:  streamlit run app.py      (needs streamlit >= 1.40)
"""

import html as html_lib
import re
import time

import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

import kg_rag  # connect(), search_graph(), create_rag_chain(), graph_summary(), PERSON, STOP_WORDS

st.set_page_config(page_title="Ratan Tata · Knowledge Graph", page_icon="🕸️", layout="wide",
                   initial_sidebar_state="collapsed")

COLORS = {"Query": "#E4572E", "Person": "#1F3A5F", "Topic": "#C9A227", "FAQ": "#4F86C6", "Answer": "#94A3B8"}
SIZES = {"Query": 22, "Person": 30, "Topic": 20, "FAQ": 14, "Answer": 10}
LEVEL = {"Person": 0, "Topic": 1, "Query": 1, "FAQ": 2, "Answer": 3}   # graph columns, left -> right
TOP = 58          # px used by the title bar
GAP = 12          # px between panels

# ---------- Look ----------
st.markdown(
    f"""
    <style>
    /* no sidebar, no Streamlit chrome: the app owns the whole window */
    #MainMenu, footer, [data-testid="stAppDeployButton"], [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"] {{display: none !important;}}
    [data-testid="stHeader"] {{height: 0; background: transparent;}}
    html, body, .stApp {{background: #EEF2F7; overflow: hidden;}}
    .block-container {{max-width: 100%; padding: 10px 16px 0 16px;}}
    [data-testid="stVerticalBlock"] {{gap: {GAP}px;}}
    [data-testid="stHorizontalBlock"] {{gap: {GAP}px;}}

    /* title bar */
    .topbar {{display: flex; justify-content: space-between; align-items: center; height: {TOP - 16}px;}}
    .brand {{display: flex; align-items: baseline; gap: .7rem;}}
    .brand b {{font-family: Georgia, serif; font-size: 1.35rem; color: #1F3A5F;}}
    .brand span {{color: #64748B; font-size: .85rem;}}
    .stats {{display: flex; gap: .4rem;}}
    .stat {{background: #FFFFFF; border: 1px solid #DCE3EC; border-radius: 999px; padding: .12rem .7rem;
            font-size: .78rem; color: #64748B;}}
    .stat b {{color: #1F3A5F; margin-right: .2rem;}}

    /* the three panels */
    .st-key-graphcard, .st-key-chatcard, .st-key-querycard {{
        background: #FFFFFF; border: 1px solid #DCE3EC; border-radius: 16px;
        box-shadow: 0 6px 22px rgba(31, 58, 95, .07); padding: 10px 14px; overflow: hidden; gap: 6px !important;
    }}
    div.st-key-graphcard, div.st-key-chatcard, div.st-key-querycard {{
        height: calc(100vh - {TOP + 18}px) !important; flex: 0 0 auto !important;}}
    div.st-key-chatcard  {{display: flex !important; flex-direction: column !important;}}
    div.st-key-querycard {{overflow-y: auto !important;}}
    div.st-key-graphcard iframe {{height: calc(100vh - {TOP + 18 + 20 + 34 + 6}px) !important; width: 100%; border: 0;}}
    /* Streamlit gives markdown blocks a negative bottom margin; it made the iframe cover the panel titles */
    div.st-key-graphcard [data-testid="stMarkdownContainer"], div.st-key-chatcard [data-testid="stMarkdownContainer"],
    div.st-key-querycard [data-testid="stMarkdownContainer"] {{margin-bottom: 0 !important;}}

    .head {{display: flex; justify-content: space-between; align-items: center; gap: 8px;
             height: 34px; border-bottom: 1px solid #EEF2F7; margin-bottom: 2px; overflow: hidden; white-space: nowrap;}}
    .head .left {{display: flex; align-items: center; gap: 8px; min-width: 0;}}
    .head .t {{font-weight: 700; color: #1F3A5F; font-size: .92rem;}}
    .legend {{display: flex; flex-wrap: nowrap; overflow: hidden;}}
    .legend span {{display: inline-flex; align-items: center; gap: 4px; margin-left: 9px; font-size: .72rem; color: #475569;}}
    .legend i {{width: 9px; height: 9px; border-radius: 50%; display: inline-block;}}
    .badge {{font-size: .74rem; font-weight: 600; border-radius: 999px; padding: .1rem .6rem;}}
    .badge.live {{background: #FFF1EB; color: #B4441F; display: inline-flex; align-items: center; gap: .35rem;}}
    .badge.live i {{width: 7px; height: 7px; border-radius: 50%; background: #E4572E; animation: pulse 1.2s infinite;}}
    .badge.done {{background: #EAF6EC; color: #2E7D32;}}
    .badge.idle {{background: #F1F5F9; color: #64748B;}}
    @keyframes pulse {{0% {{box-shadow: 0 0 0 0 rgba(228,87,46,.6);}} 70% {{box-shadow: 0 0 0 7px rgba(228,87,46,0);}} 100% {{box-shadow: 0 0 0 0 rgba(228,87,46,0);}}}}

    /* chat window: messages scroll (auto-scrolled to the newest), input pinned below */
    div.st-key-chatmsgs {{flex: 1 1 0 !important; overflow-y: auto !important;
                          min-height: 0 !important; height: auto !important; padding-right: 4px;}}
    div.st-key-jsbox, div:has(> div.st-key-jsbox) {{display: none !important;}}
    div.st-key-chatcard > div:has(div.st-key-chatmsgs) {{flex: 1 1 0 !important; min-height: 0 !important; display: flex; flex-direction: column;}}
    .st-key-chatmsgs [data-testid="stChatMessage"] {{padding: .35rem .6rem; border-radius: 12px; gap: .5rem;}}
    .st-key-chatmsgs [data-testid="stChatMessage"] p {{font-size: .88rem; line-height: 1.45; margin-bottom: .2rem;}}
    .st-key-chatmsgs [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{background: #F1F5F9;}}
    .st-key-chatcard [data-testid="stChatInput"] {{border: 2px solid #1F3A5F; border-radius: 12px; flex: 0 0 auto;}}
    .hint {{color: #94A3B8; font-size: .85rem; padding: .4rem .2rem;}}
    .meta {{color: #94A3B8; font-size: .72rem;}}
    .st-key-chatmsgs .stButton button {{font-size: .72rem; padding: 0 .5rem; min-height: 1.5rem; border-radius: 999px;}}

    /* query section */
    .q {{font-size: .95rem; font-weight: 600; color: #1F2937; margin: .1rem 0 .3rem;}}
    .chip {{display: inline-block; background: #FDF3D6; color: #8A6B0F; border-radius: 999px;
            padding: 0 .5rem; font-size: .72rem; margin: 0 .25rem .25rem 0;}}
    .chip.faq {{background: #E8F0FA; color: #2F5E96;}}
    .st-key-querycard pre {{font-size: .7rem;}}
    .st-key-querycard pre code {{white-space: pre-wrap !important; word-break: break-word;}}
    .st-key-querycard .stTabs [data-baseweb="tab"] {{font-size: .78rem; padding: .1rem .35rem; height: 1.9rem;}}

    /* searching animation shown in the graph panel */
    .scan {{display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .9rem;
             height: calc(100vh - {TOP + 70}px);}}
    .scan .dots {{display: flex; gap: 24px;}}
    .scan .dots i {{width: 14px; height: 14px; border-radius: 50%; animation: blink 1.2s infinite ease-in-out;}}
    .scan .dots i:nth-child(1) {{background: #1F3A5F;}}
    .scan .dots i:nth-child(2) {{background: #C9A227; animation-delay: .15s;}}
    .scan .dots i:nth-child(3) {{background: #4F86C6; animation-delay: .3s;}}
    .scan .dots i:nth-child(4) {{background: #94A3B8; animation-delay: .45s;}}
    .scan span {{color: #64748B; font-size: .85rem;}}
    @keyframes blink {{0%, 100% {{opacity: .25; transform: scale(.8);}} 50% {{opacity: 1; transform: scale(1.1);}}}}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Neo4j + LLM (created once) ----------
@st.cache_resource
def get_driver():
    return kg_rag.connect()


@st.cache_resource
def get_chain():
    return kg_rag.create_rag_chain()


@st.cache_data(ttl=600)
def fetch_full_graph(_driver):
    """Person -> Topic -> FAQ for the overview shown before any question."""
    cypher = """
        MATCH (p:Person)-[:HAS_TOPIC]->(t:Topic)-[:HAS_FAQ]->(q:FAQ)
        RETURN p.name AS person, t.name AS topic, q.question AS question
    """
    with _driver.session() as session:
        rows = [dict(r) for r in session.run(cypher)]
    nodes, edges = {}, []
    for r in rows:
        nodes[("Person", r["person"])] = r["person"]
        nodes[("Topic", r["topic"])] = r["topic"]
        nodes[("FAQ", r["question"])] = r["question"]
        edges.append((("Person", r["person"]), ("Topic", r["topic"]), "HAS_TOPIC"))
        edges.append((("Topic", r["topic"]), ("FAQ", r["question"]), "HAS_FAQ"))
    return nodes, list(dict.fromkeys(edges))


def query_subgraph(question, facts):
    """Only the nodes connected to the current question."""
    q_key = ("Query", question)
    nodes, edges = {q_key: question}, []
    for f in facts:
        person, topic = ("Person", kg_rag.PERSON), ("Topic", f["topic"])
        faq, ans = ("FAQ", f["question"]), ("Answer", f["answer"])
        nodes.update({person: kg_rag.PERSON, topic: f["topic"], faq: f["question"], ans: f["answer"]})
        edges += [(person, topic, "HAS_TOPIC"), (topic, faq, "HAS_FAQ"),
                  (faq, ans, "HAS_ANSWER"), (q_key, faq, "MATCHED")]
    return nodes, list(dict.fromkeys(edges))


def short(text, n):
    return text if len(text) <= n else text[: n - 1] + "…"


# Subtle entrance: layout is computed first, then columns fade in left -> right and the view eases in.
ANIMATION_JS = """
<script>
(function () {
  if (typeof network === "undefined") return;
  network.once("stabilizationIterationsDone", function () { network.setOptions({physics: false}); });
  var all = nodes.get();
  nodes.update(all.map(function (n) { return {id: n.id, opacity: 0}; }));
  function fade(ids, start) {
    var t0 = null;
    function step(ts) {
      if (!t0) t0 = ts;
      var k = Math.min((ts - t0) / 260, 1);
      nodes.update(ids.map(function (id) { return {id: id, opacity: k}; }));
      if (k < 1) requestAnimationFrame(step);
    }
    setTimeout(function () { requestAnimationFrame(step); }, start);
  }
  setTimeout(function () {            // wait until the panel has its final size
    network.setSize("100%", window.innerHeight + "px");
    network.redraw();
    network.fit({animation: false, maxZoomLevel: 1.8});
    var target = {position: network.getViewPosition(), scale: Math.min(network.getScale() * 0.95, 1.8)};
    network.moveTo({position: target.position, scale: target.scale * 0.94, animation: false});
    var levels = Array.from(new Set(all.map(function (n) { return n.lvl || 0; }))).sort();
    levels.forEach(function (lv, i) {
      fade(all.filter(function (n) { return (n.lvl || 0) === lv; }).map(function (n) { return n.id; }), 40 + i * 150);
    });
    network.moveTo({position: target.position, scale: target.scale,
                    animation: {duration: 700, easingFunction: "easeOutCubic"}});
  }, 80);
})();
</script>
"""


def build_pyvis(nodes, edges, query_view):
    """PyVis network -> HTML. Short labels (full text on hover) so nothing overlaps."""
    net = Network(height="100vh", width="100%", bgcolor="#FFFFFF", font_color="#1F2937",
                  directed=True, cdn_resources="in_line")
    ids = {key: i for i, key in enumerate(nodes)}
    for key, text in nodes.items():
        kind = key[0]
        if query_view:
            label = {"Query": "❓ " + short(text, 22), "Person": text, "Topic": text,
                     "FAQ": short(text, 28), "Answer": short(text, 26)}[kind]
        else:   # overview: only Person and Topic names, FAQs on hover
            label = text if kind in ("Person", "Topic") else ""
        node = dict(
            label=label, title=f"{kind}: {text}", lvl=LEVEL[kind],
            shape="star" if kind == "Query" else "dot",
            color={"background": COLORS[kind], "border": "#FFFFFF",
                   "highlight": {"background": COLORS[kind], "border": "#111827"}},
            borderWidth=2, size=SIZES[kind],
            shadow={"enabled": True, "size": 8, "x": 0, "y": 2, "color": "rgba(0,0,0,0.10)"},
            font={"size": 13 if kind in ("Person", "Topic", "Query") else 11,
                  "face": "Inter, Arial", "bold": kind in ("Person", "Topic", "Query")},
            widthConstraint={"maximum": 118},
        )
        if query_view:
            node["level"] = LEVEL[kind]
        net.add_node(ids[key], **node)

    for src, dst, rel in edges:
        matched = rel == "MATCHED"
        net.add_edge(ids[src], ids[dst], title=rel,
                     color={"color": "#E4572E" if matched else "#CBD5E1", "highlight": "#1F3A5F"},
                     width=2.4 if matched else 1.3, dashes=[8, 6] if matched else False,
                     arrows={"to": {"enabled": True, "scaleFactor": 0.55}})

    if query_view:
        options = """
        {"layout": {"hierarchical": {"enabled": true, "direction": "LR", "sortMethod": "directed",
                                     "levelSeparation": 155, "nodeSpacing": 118, "treeSpacing": 110}},
         "physics": {"enabled": false},
         "edges": {"smooth": {"type": "cubicBezier", "forceDirection": "horizontal", "roundness": 0.5}},
         "interaction": {"hover": true, "tooltipDelay": 80}}
        """
    else:
        options = """
        {"physics": {"enabled": true, "solver": "forceAtlas2Based",
                     "forceAtlas2Based": {"gravitationalConstant": -70, "springLength": 90,
                                          "springConstant": 0.07, "avoidOverlap": 0.8},
                     "stabilization": {"enabled": true, "iterations": 400, "fit": true}},
         "edges": {"smooth": {"type": "continuous"}},
         "interaction": {"hover": true, "tooltipDelay": 80}}
        """
    net.set_options(options)
    page_css = ("<style>html,body{margin:0;overflow:hidden}#mynetwork,.card{border:none!important;"
                "box-shadow:none!important;margin:0!important}</style>")
    return (net.generate_html().replace("border: 1px solid lightgray;", "border: none;")
            .replace("</head>", page_css + "</head>")
            .replace("<body>", '<body style="margin:0;overflow:hidden">')
            .replace("</body>", ANIMATION_JS + "</body>"))


def keywords_for(question):
    """Same keyword logic as kg_rag.search_graph()."""
    words = re.findall(r"\w+", question.lower())
    return [w for w in words if w not in kg_rag.STOP_WORDS and len(w) > 2] or ["who is ratan tata"]


def cypher_list(items):
    return "[" + ", ".join("'" + i.replace("\\", "\\\\").replace("'", "\\'") + "'" for i in items) + "]"


def search_cypher(question):
    """The exact search query sent to Neo4j, keywords filled in (paste-able in Neo4j Browser)."""
    kw = cypher_list(keywords_for(question))
    return f"""MATCH (p:Person)-[:HAS_TOPIC]->(t:Topic)-[:HAS_FAQ]->(q:FAQ)-[:HAS_ANSWER]->(a:Answer)
WITH t, q, a,
     size([k IN {kw} WHERE toLower(q.question) CONTAINS k]) * 3 +
     size([k IN {kw} WHERE toLower(t.name) CONTAINS k]) * 2 +
     size([k IN {kw} WHERE toLower(a.text) CONTAINS k]) AS score
WHERE score > 0
RETURN t.name AS topic, q.question AS question, a.text AS answer, score
ORDER BY score DESC
LIMIT 5"""


def subgraph_cypher(facts):
    return f"""MATCH p=(:Person)-[:HAS_TOPIC]->(:Topic)-[:HAS_FAQ]->(q:FAQ)-[:HAS_ANSWER]->(:Answer)
WHERE q.question IN {cypher_list([f["question"] for f in facts])}
RETURN p"""


def build_context(facts):
    if not facts:
        return "(No relevant information found in the Knowledge Graph)"
    return "\n\n".join(f"Topic: {f['topic']}\nQuestion: {f['question']}\nAnswer: {f['answer']}" for f in facts)


def badge(state, n=0):
    return {
        "idle": '<span class="badge idle">Overview</span>',
        "searching": '<span class="badge live"><i></i>Searching…</span>',
        "thinking": f'<span class="badge live"><i></i>{n} facts · answering…</span>',
        "done": f'<span class="badge done">✓ {n} facts</span>',
    }[state]


# ---------- Session + connection ----------
st.session_state.setdefault("messages", [])   # [{question, answer, facts, secs}]
st.session_state.setdefault("current", None)  # {question, facts} drawn in the graph

try:
    driver = get_driver()
except Exception as e:
    st.error(f"Could not connect to Neo4j. Check NEO4J_URI / USERNAME / PASSWORD in `.env`.\n\n{e}")
    st.stop()
summary = kg_rag.graph_summary(driver)
total = sum(s["faqs"] for s in summary)

# ---------- Title bar ----------
st.markdown(
    f"""<div class="topbar">
      <div class="brand"><b>Ratan Tata · Knowledge Graph</b><span>Ask a question — watch which nodes answer it</span></div>
      <div class="stats"><span class="stat"><b>{len(summary)}</b>topics</span>
        <span class="stat"><b>{total}</b>FAQs</span>
        <span class="stat"><b>{len(summary) + total * 2}</b>relations</span>
        <span class="stat"><b>🤖</b>{kg_rag.LLM_MODEL}</span></div></div>""",
    unsafe_allow_html=True,
)

# Keeps the chat window scrolled to the newest message (runs in a hidden iframe on the same origin).
SCROLL_JS = """<script>
setInterval(function () {
  try {
    var el = window.parent.document.querySelector('.st-key-chatmsgs');
    if (!el) return;
    if (el.dataset.h !== String(el.scrollHeight)) { el.scrollTop = el.scrollHeight; el.dataset.h = el.scrollHeight; }
  } catch (e) {}
}, 250);
</script>"""
with st.container(key="jsbox"):
    components.html(SCROLL_JS, height=0)

chat_col, graph_col, query_col = st.columns([1, 1.9, 1.05])

# ---------- Section 1: chat window ----------
with chat_col:
    with st.container(key="chatcard"):
        st.markdown('<div class="head"><span class="t">💬 Chat</span></div>', unsafe_allow_html=True)
        msgs_box = st.container(key="chatmsgs")
        question = st.chat_input("Ask about Ratan Tata…")

# ---------- Section 2: graph ----------
with graph_col:
    with st.container(key="graphcard"):
        head_ph = st.empty()
        graph_ph = st.empty()

# ---------- Section 3: query ----------
with query_col:
    with st.container(key="querycard"):
        st.markdown('<div class="head"><span class="t">🔎 Query</span></div>', unsafe_allow_html=True)
        query_ph = st.empty()


def graph_head(state, n=0):
    legend = "".join(f'<span><i style="background:{c}"></i>{k}</span>' for k, c in COLORS.items())
    head_ph.markdown(f'<div class="head"><span class="left"><span class="t">🕸️ Knowledge graph</span>{badge(state, n)}</span>'
                     f'<span class="legend">{legend}</span></div>', unsafe_allow_html=True)


def draw_graph(cur):
    if cur:
        nodes, edges = query_subgraph(cur["question"], cur["facts"])
        html = build_pyvis(nodes, edges, query_view=True)
    else:
        nodes, edges = fetch_full_graph(driver)
        html = build_pyvis(nodes, edges, query_view=False) if nodes else ""
    with graph_ph.container():
        if html:
            components.html(html, height=560, scrolling=False)
        else:
            st.info("The graph is empty — run `python kg_rag.py` once to load FAQ.txt.")


def draw_query(question, facts, searching=False):
    with query_ph.container():
        if question is None:
            st.markdown('<div class="hint">The Cypher query sent to Neo4j for your question will appear here.</div>',
                        unsafe_allow_html=True)
            return
        topics = "".join(f'<span class="chip">{html_lib.escape(t)}</span>' for t in dict.fromkeys(f["topic"] for f in facts))
        faqs = "".join(f'<span class="chip faq">{html_lib.escape(short(f["question"], 44))}</span>' for f in facts)
        if not facts and not searching:
            topics = '<span class="chip">no matching nodes</span>'
        st.markdown(f'<div class="q">❓ {html_lib.escape(question)}</div><div>{topics}{faqs}</div>',
                    unsafe_allow_html=True)
        t1, t2 = st.tabs(["Search Cypher", "View in Neo4j Browser"])
        with t1:
            st.code(search_cypher(question), language="cypher")
        with t2:
            if facts:
                st.code(subgraph_cypher(facts), language="cypher")
            else:
                st.caption("No matching nodes.")


def render_history(box, show_hint=True):
    """All earlier messages, oldest first (the window auto-scrolls to the newest)."""
    msgs = st.session_state.messages
    cur_q = (st.session_state.current or {}).get("question")
    with box:
        for i, m in enumerate(msgs):
            with st.chat_message("user"):
                st.markdown(m["question"])
            with st.chat_message("assistant"):
                st.markdown(m["answer"])
                st.markdown(f'<span class="meta">{len(m["facts"])} graph facts · {m["secs"]:.0f}s</span>',
                            unsafe_allow_html=True)
                if m["question"] != cur_q and st.button("🕸️ Show in graph", key=f"show_{i}"):
                    st.session_state.current = {"question": m["question"], "facts": m["facts"]}
                    st.rerun()
        if not msgs and show_hint:
            st.markdown('<div class="hint">👋 Ask anything about Ratan Tata — e.g. <i>What did he acquire '
                        'abroad?</i> The graph will show exactly which nodes the answer came from.</div>',
                        unsafe_allow_html=True)


# ---------- New question: search -> draw graph -> stream answer ----------
if question:
    render_history(msgs_box, show_hint=False)
    with msgs_box:
        with st.chat_message("user"):
            st.markdown(question)
        bot = st.chat_message("assistant")
    with bot:
        status = st.empty()
        status.markdown('<span class="meta">🔎 Searching the knowledge graph…</span>', unsafe_allow_html=True)
    graph_head("searching")
    draw_query(question, [], searching=True)
    graph_ph.markdown('<div class="scan"><div class="dots"><i></i><i></i><i></i><i></i></div>'
                      '<span>Walking the graph: Ratan Tata → topics → FAQs → answers…</span></div>',
                      unsafe_allow_html=True)

    start = time.time()
    try:
        facts = kg_rag.search_graph(driver, question)
    except Exception as e:
        status.error(f"Neo4j search failed: {e}")
        st.stop()
    st.session_state.current = {"question": question, "facts": facts}

    graph_head("thinking", len(facts))
    draw_query(question, facts)
    draw_graph(st.session_state.current)
    status.markdown(f'<span class="meta">🕸️ {len(facts)} facts found · 🤖 writing the answer…</span>',
                    unsafe_allow_html=True)

    with bot:
        try:
            stream = (chunk.content for chunk in
                      get_chain().stream({"context": build_context(facts), "question": question}))
            answer = st.write_stream(stream)
        except Exception as e:
            st.error(f"Ollama error: is it running? (`ollama serve`)\n\n{e}")
            st.stop()
    secs = time.time() - start
    status.empty()
    with bot:
        st.markdown(f'<span class="meta">{len(facts)} graph facts · {secs:.0f}s</span>', unsafe_allow_html=True)
    graph_head("done", len(facts))
    st.session_state.messages.append({"question": question, "answer": answer, "facts": facts, "secs": secs})

# ---------- Otherwise: show the current state ----------
else:
    cur = st.session_state.current
    render_history(msgs_box)
    if cur:
        graph_head("done", len(cur["facts"]))
        draw_query(cur["question"], cur["facts"])
    else:
        graph_head("idle")
        draw_query(None, [])
    draw_graph(cur)