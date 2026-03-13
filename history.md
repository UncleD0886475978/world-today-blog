---
layout: default
title: History & Analysis
permalink: /history/
---
<h2>History & Analysis</h2>
<ul>
{% for post in site.posts %}
  {% if post.categories contains "History & Analysis" %}
    <li><span style="color:#999;font-size:0.85em;">{{ post.date | date: "%B %d, %Y" }}</span> — <a href="{{ post.url | prepend: site.baseurl }}">{{ post.title }}</a></li>
  {% endif %}
{% endfor %}
</ul>
