import json
import sys
import webbrowser
from pathlib import Path

from parser import parse, MiniCError
from ast_nodes import AstNode


def node_label(node):
    scalars = []
    for attr in node.attrs:
        value = getattr(node, attr)
        if value is not None and not isinstance(value, (AstNode, list)):
            scalars.append(str(value))
    name = type(node).__name__
    return f"{name}: {' '.join(scalars)}" if scalars else name


def ast_to_dict(node, role=None):
    result = {
        'type': type(node).__name__,
        'label': node_label(node),
        'role': role,
        'line': node.lineno,
        'children': [],
    }
    for attr in node.attrs:
        value = getattr(node, attr)
        if isinstance(value, AstNode):
            result['children'].append(ast_to_dict(value, attr))
        elif isinstance(value, list):
            for item in value:
                result['children'].append(ast_to_dict(item, attr))
    return result


def ast_to_json(tree, indent=2):
    return json.dumps(ast_to_dict(tree), ensure_ascii=False, indent=indent)


HTML_TEMPLATE = r'''<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AST: __TITLE__</title>
<style>
  :root {
    --bg:  #cdeed6; --panel: #ffffff; --fg: #1d2330; --muted: #3f5a4a; --line: #2f6f4f;
    --stmt: #3d6fd6; --expr: #e0892b; --leaf: #2f9e6f; --border: #d9dde5;
    color-scheme: light;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body { background: var(--bg); color: var(--fg);
         font: 14px/1.4 "Segoe UI";
         display: flex; flex-direction: column; }
  header { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 20px; padding: 22px 28px;
           background: #cdeed6;}
  h1 { font-size: 20px; font-weight: 600; margin: 0; }
  .spacer { flex: 1; }
 button { font: inherit; font-size: 15px; color: #fff; background: #1f6f4a; border: 1px solid #1f6f4a;
           border-radius: 8px; padding: 8px 16px; cursor: pointer; }
  button:hover { filter: brightness(1.1); }
  button:focus-visible { outline: 2px solid var(--stmt); outline-offset: 1px; }
 .legend { display: flex; flex-wrap: wrap; gap: 14px 24px; color: #111; font-size: 17px; }
  .legend span::before { content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 50%;
                         margin-right: 6px; background: var(--c); vertical-align: -1px; }
  main { flex: 1; min-height: 0; }
  svg { width: 100%; height: 100%; display: block; cursor: grab; }
  svg:active { cursor: grabbing; }
  .link { fill: none; stroke: var(--line); stroke-width: 1.3; }
  .role { fill: var(--muted); font-size: 10px; text-anchor: middle; paint-order: stroke;
          stroke: var(--bg); stroke-width: 3px; }
  .node circle { stroke: var(--bg); stroke-width: 2; cursor: pointer; }
  .node.collapsed circle { stroke: var(--fg); stroke-width: 2; }
  .node text { fill: var(--fg); font-size: 12px; paint-order: stroke; stroke: var(--bg); stroke-width: 3px; }
  #tip { position: fixed; pointer-events: none; background: var(--panel); color: var(--fg);
         border: 1px solid var(--border); border-radius: 6px; padding: 6px 9px; font-size: 12px;
         opacity: 0; transition: opacity .1s; max-width: 260px; }
</style>
</head>
<body>
<header>
  <h1>AST: __TITLE__</h1>
  <div class="legend">
    <span style="--c: var(--stmt)">оператори</span>
    <span style="--c: var(--expr)">вирази</span>
    <span style="--c: var(--leaf)">літерали й змінні</span>
  </div>
  <span class="spacer"></span>
  <button id="expand">Розгорнути все</button>
  <button id="collapse">Згорнути до рівня 2</button>
  <button id="fit">Вмістити в екран</button>
</header>
<main><svg id="chart" role="img" aria-label="Абстрактне синтаксичне дерево"></svg></main>
<div id="tip"></div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js"></script>
<script>
const DATA = __DATA__;

const KIND = {
  Root: 'stmt', Compound: 'stmt', Declaration: 'stmt', Assignment: 'stmt', PrintStmt: 'stmt',
  IfStmt: 'stmt', WhileStmt: 'stmt',
  BinaryExpr: 'expr', UnaryExpr: 'expr',
  NumberLit: 'leaf', Identifier: 'leaf'
};
const fill = d => `var(--${KIND[d.data.type] || 'stmt'})`;

const svg = d3.select('#chart');
const g = svg.append('g');
const zoom = d3.zoom().scaleExtent([0.1, 3]).on('zoom', e => g.attr('transform', e.transform));
svg.call(zoom).on('dblclick.zoom', null);

const root = d3.hierarchy(DATA);
const tree = d3.tree().nodeSize([30, 250]);
const linkPath = d3.linkHorizontal().x(d => d.y).y(d => d.x);
const tip = d3.select('#tip');

function toggle(d) {
  if (d.children) { d._children = d.children; d.children = null; }
  else if (d._children) { d.children = d._children; d._children = null; }
}

function draw() {
  tree(root);
  g.selectAll('*').remove();

  g.selectAll('path.link').data(root.links()).join('path')
    .attr('class', 'link').attr('d', linkPath);

  g.selectAll('text.role')
    .data(root.links().filter(l => l.target.data.role && l.target.data.role !== 'statements'))
    .join('text').attr('class', 'role')
    .attr('x', l => (l.source.y + l.target.y) / 2)
    .attr('y', l => (l.source.x + l.target.x) / 2 - 4)
    .text(l => l.target.data.role);

  const node = g.selectAll('g.node').data(root.descendants()).join('g')
    .attr('class', d => 'node' + (d._children ? ' collapsed' : ''))
    .attr('transform', d => `translate(${d.y},${d.x})`)
    .on('click', (e, d) => { if (d.children || d._children) { toggle(d); draw(); } })
    .on('mousemove', (e, d) => {
      tip.style('opacity', 1).style('left', (e.clientX + 14) + 'px').style('top', (e.clientY + 14) + 'px')
         .html(`<b>${d.data.type}</b><br>рядок: ${d.data.line}` +
               (d.data.role ? `<br>поле: ${d.data.role}` : '') +
               (d._children ? `<br>згорнуто вузлів: ${d._children.length}` : ''));
    })
    .on('mouseleave', () => tip.style('opacity', 0));

  node.append('circle').attr('r', d => d._children ? 7 : 5).attr('fill', fill);
  node.append('text')
    .attr('text-anchor', 'middle')
    .attr('y', -12)
    .text(d => d.data.label + (d._children ? ' [+]' : ''));
}

function fit() {
  const box = g.node().getBBox();
  const w = svg.node().clientWidth, h = svg.node().clientHeight;
  const k = Math.min(w / (box.width + 80), h / (box.height + 80), 1.6);
  const tx = (w - box.width * k) / 2 - box.x * k;
  const ty = (h - box.height * k) / 2 - box.y * k;
  svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity.translate(tx, ty).scale(k));
}

function setDepth(maxDepth) {
  root.each(d => {
    if (d._children) { d.children = d._children; d._children = null; }
  });
  if (maxDepth !== null) {
    root.each(d => { if (d.depth >= maxDepth && d.children) toggle(d); });
  }
  draw();
  fit();
}

document.getElementById('expand').onclick = () => setDepth(null);
document.getElementById('collapse').onclick = () => setDepth(2);
document.getElementById('fit').onclick = fit;
window.addEventListener('resize', fit);

draw();
fit();
</script>
</body>
</html>
'''


def render_html(tree, title='program'):
    data = ast_to_json(tree, indent=None)
    data = data.replace('</', '<\\/')
    return HTML_TEMPLATE.replace('__TITLE__', title).replace('__DATA__', data)


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith('-'):
        print("Usage: python src/visualize.py <file.c> [-o ast.html] [--json ast.json] [--no-open]",
              file=sys.stderr)
        return 2

    src_path = Path(args[0])
    out_html = Path(args[args.index('-o') + 1]) if '-o' in args else Path('ast.html')
    out_json = Path(args[args.index('--json') + 1]) if '--json' in args else None

    source = src_path.read_text(encoding='utf-8')
    try:
        tree = parse(source)
    except MiniCError as e:
        print(f"{e.kind} (line {e.line}, column {e.column}): {e.msg}", file=sys.stderr)
        return 1

    out_html.write_text(render_html(tree, src_path.name), encoding='utf-8')
    print(f"Generated {out_html}")

    if out_json is not None:
        out_json.write_text(ast_to_json(tree), encoding='utf-8')
        print(f"Generated {out_json}")

    if '--no-open' not in args:
        webbrowser.open(out_html.resolve().as_uri())
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))