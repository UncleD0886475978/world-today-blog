---
layout: default
title: "🔍 Crime & Justice"
permalink: /crime/
---
<div style="background:var(--nav-bg);color:#fff;padding:3rem 1.5rem 2rem;"><div style="max-width:var(--max);margin:0 auto;"><div style="font-family:var(--f-ui);font-size:.62rem;font-weight:800;letter-spacing:.25em;text-transform:uppercase;color:var(--r-conflict);margin-bottom:.5rem;">Crime & Justice</div><h1 style="font-family:var(--f-display);font-size:clamp(2rem,5vw,3.2rem);font-weight:900;color:#fff;">🔍 Crime & Justice</h1></div></div>
<div class="main-wrap"><div class="posts-grid">{% assign posts = site.posts | where_exp: "post", "post.categories contains 'Crime & Justice'" %}{% if posts.size > 0 %}{% for post in posts %}<div class="card" style="--stripe-color:var(--r-conflict)"><div class="card-tag">🔍 Crime & Justice</div><h3><a href="{{ post.url | prepend: site.baseurl }}">{{ post.title }}</a></h3><p>{{ post.excerpt | strip_html | truncate: 120 }}</p><time>{{ post.date | date: "%B %d, %Y" }}</time></div>{% endfor %}{% else %}<p style="color:var(--ink4);font-family:var(--f-ui);padding:2rem;">Crime & Justice stories coming soon — check back after the 19:00 UTC run.</p>{% endif %}</div></div>
