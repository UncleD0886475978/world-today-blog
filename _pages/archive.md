---
layout: default
title: Archive
permalink: /archive/
---
<div style="background:var(--nav-bg);color:#fff;padding:3rem 1.5rem 2.5rem;"><div style="max-width:900px;margin:0 auto;"><div style="font-family:var(--f-ui);font-size:.62rem;font-weight:800;letter-spacing:.25em;text-transform:uppercase;color:rgba(255,255,255,.3);margin-bottom:.75rem;">The World Today</div><h1 style="font-family:var(--f-display);font-size:clamp(2rem,5vw,3.5rem);font-weight:900;color:#fff;">Story Archive</h1><p style="color:rgba(255,255,255,.5);font-size:.9rem;margin-top:.75rem;">{{ site.posts | size }} stories published</p></div></div>
<div class="archive-wrap">{% assign postsByYear = site.posts | group_by_exp: "post", "post.date | date: '%Y'" %}{% for year in postsByYear %}<div class="archive-year">{{ year.name }}</div>{% assign postsByMonth = year.items | group_by_exp: "post", "post.date | date: '%B'" %}{% for month in postsByMonth %}<div class="archive-month"><div class="archive-month-label">{{ month.name }} {{ year.name }}</div>{% for post in month.items %}<div class="archive-item"><time>{{ post.date | date: "%b %d" }}</time><span class="arc-cat">{{ post.categories[0] }}</span><a href="{{ post.url | prepend: site.baseurl }}">{{ post.title }}</a></div>{% endfor %}</div>{% endfor %}{% endfor %}</div>
