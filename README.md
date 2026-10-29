<img src="./assets/hero.svg" width="100%" alt="nvana — building quiet machines for loud numbers" />

`fintech` · `real-time` · `dataviz` · `cloud` · `ai`

Full-stack, end to end — interfaces that make dense data feel obvious, services that stay boring under load, and infrastructure written down rather than clicked. Paris 🇫🇷 → Oslo 🇳🇴.

<div align="center">
  <img src="./assets/orbit.svg" width="62%" alt="orbiting tech stack" />
</div>

### 🚨 03:12 — prod is down

The pager screams. p99 latency is 40s, error rate 60%, and the trading desk opens in five hours. **What do you do?**

<details><summary>🔁 Restart everything</summary>
<blockquote>

Everything comes back… for 90 seconds. Then it falls over again. Your on-call buddy is now awake, and not happy.

<details><summary>🔁 Restart again, harder</summary>
<blockquote>

💀 **Game over.** You have invented the outage loop. *Refresh to try again.*

</blockquote>
</details>
<details><summary>📜 Fine, read the logs</summary>
<blockquote>

Someone already did. *"connection pool exhausted"* — your buddy found it while you were restarting things. They take it from here.

🥉 **Bronze.** Fixed, but not by you. *Refresh to try again.*

</blockquote>
</details>
</blockquote>
</details>

<details><summary>📜 Read the logs</summary>
<blockquote>

A waterfall of `connection pool exhausted`. Something is hogging the database.

<details><summary>📈 Scale the database up</summary>
<blockquote>

Bigger box, same error — the pool is still 10 connections. The cloud bill doubles anyway.

💀 **Game over.** *Refresh to try again.*

</blockquote>
</details>
<details><summary>🔍 Find who is holding the connections</summary>
<blockquote>

One query holds 9 of 10 connections: a `SELECT *` on `trades` with no index, fired by a dashboard someone opened at 03:10.

<details><summary>🔪 Kill the query and go back to bed</summary>
<blockquote>

Graphs go green. You sleep. At 03:10 tomorrow, the dashboard opens again.

🥈 **Silver.** See you tomorrow night. *Refresh to try again.*

</blockquote>
</details>
<details><summary>🗂️ Kill the query, add the index, then sleep</summary>
<blockquote>

The query drops from 38s to 4ms. Graphs go green and stay green. You write a two-line postmortem and go back to bed.

🏆 **Gold. Incident closed.** Nobody at the trading desk ever knows.

</blockquote>
</details>
<details><summary>🫵 Find out who opened that dashboard</summary>
<blockquote>

You check the access logs. It was you, at 03:10, checking whether everything was fine.

💀 **Game over.** *Refresh to try again.*

</blockquote>
</details>
</blockquote>
</details>
</blockquote>
</details>

<details><summary>🔕 Mute the pager</summary>
<blockquote>

💀 **Game over.** You wake up at 09:00 to 47 missed calls. *Refresh to try again.*

</blockquote>
</details>
