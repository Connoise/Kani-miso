/**
 * D3.js Force-directed graph visualization for Kani-miso
 */

function initGraph(containerId, dataUrl) {
  const container = document.getElementById(containerId);
  const width = container.clientWidth;
  const height = 600;

  const svg = d3.select(`#${containerId}`)
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  // Zoom behavior
  const g = svg.append('g');
  const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on('zoom', (event) => {
      g.attr('transform', event.transform);
    });

  svg.call(zoom);

  // Reset zoom button
  document.getElementById('reset-zoom').addEventListener('click', () => {
    svg.transition().duration(750).call(
      zoom.transform,
      d3.zoomIdentity.translate(width / 2, height / 2).scale(1)
    );
  });

  // Load data
  d3.json(dataUrl).then(data => {
    // Performance warning
    if (data.nodes.length > 5000) {
      const warning = document.getElementById('graph-warning');
      warning.textContent = `Large graph detected (${data.nodes.length} nodes). Consider filtering by hub or using local view for better performance.`;
      warning.style.display = 'block';
    }

    // Hub-centric force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links)
        .id(d => d.id)
        .distance(d => {
          // Hub-connected links get more space
          return (d.source.type === 'hub' || d.target.type === 'hub') ? 100 : 80;
        }))
      .force('charge', d3.forceManyBody()
        .strength(d => d.type === 'hub' ? -400 : -200))  // Stronger repulsion for hubs
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide()
        .radius(d => d.type === 'hub' ? 25 : 15));

    // Optional radial force for hubs
    const hubNodes = data.nodes.filter(d => d.type === 'hub');
    if (hubNodes.length > 0) {
      simulation.force('radial', d3.forceRadial()
        .radius(200)
        .strength(d => d.type === 'hub' ? 0.1 : 0));
    }

    // Define arrow markers for directed edges
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 8)
      .attr('markerHeight', 8)
      .append('svg:path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#999');

    // Links with arrows
    const link = g.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('class', 'graph-link')
      .attr('marker-end', 'url(#arrowhead)');

    // Nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(data.nodes)
      .join('circle')
      .attr('r', d => d.type === 'hub' ? 12 : 8)
      .attr('class', d => `graph-node node-${d.type}`)
      .call(drag(simulation))
      .on('click', (event, d) => {
        window.location.href = `/note/${d.id}`;
      })
      .on('mouseover', function(event, d) {
        // Show tooltip
        d3.select(this).attr('r', d => d.type === 'hub' ? 15 : 10);

        // Highlight connected nodes
        const connectedNodes = new Set();
        connectedNodes.add(d.id);

        link.each(function(l) {
          if (l.source.id === d.id || l.target.id === d.id) {
            connectedNodes.add(l.source.id);
            connectedNodes.add(l.target.id);
          }
        });

        node.style('opacity', n => connectedNodes.has(n.id) ? 1 : 0.2);
        link.style('opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1);
      })
      .on('mouseout', function(event, d) {
        // Reset
        d3.select(this).attr('r', d => d.type === 'hub' ? 12 : 8);
        node.style('opacity', 1);
        link.style('opacity', 1);
      });

    // Labels (only for hubs)
    const label = g.append('g')
      .selectAll('text')
      .data(data.nodes.filter(d => d.type === 'hub'))
      .join('text')
      .text(d => d.title.substring(0, 20))
      .attr('class', 'graph-label');

    // Tick function
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);

      label
        .attr('x', d => d.x + 15)
        .attr('y', d => d.y + 4);
    });

    // Filter by type
    document.getElementById('filter-type').addEventListener('change', (e) => {
      const filterValue = e.target.value;

      if (filterValue === '') {
        node.style('display', 'block');
        label.style('display', 'block');
      } else {
        node.style('display', d => d.type === filterValue ? 'block' : 'none');
        label.style('display', d => d.type === filterValue ? 'block' : 'none');
      }
    });
  });

  function drag(simulation) {
    return d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });
  }
}
