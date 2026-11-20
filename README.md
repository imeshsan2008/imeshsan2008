<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/hero-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="./assets/hero-light.svg" />
    <img src="./assets/hero-dark.svg" alt="Imesh Sandeepa — Full-Stack Developer, Web & Graphic Designer" width="100%" />
  </picture>

  <br /><br />

  <p>
    <a href="https://imeshsan2008.github.io/"><img src="https://img.shields.io/badge/PORTFOLIO-CC0000?style=flat-square&logoColor=white" alt="Portfolio" height="28" /></a>
    <a href="https://www.linkedin.com/in/imeshsan2008/"><img src="https://img.shields.io/badge/LINKEDIN-161B22?style=flat-square&logoColor=white" alt="LinkedIn" height="28" /></a>
    <a href="https://www.instagram.com/imeshsan2008/"><img src="https://img.shields.io/badge/INSTAGRAM-161B22?style=flat-square&logo=instagram&logoColor=white" alt="Instagram" height="28" /></a>
    <a href="mailto:imeshbota0@gmail.com"><img src="https://img.shields.io/badge/GMAIL-161B22?style=flat-square&logo=gmail&logoColor=white" alt="Gmail" height="28" /></a>
    <a href="https://wa.me/94768902513?text=Hello%20from%20GitHub!"><img src="https://img.shields.io/badge/WHATSAPP-161B22?style=flat-square&logo=whatsapp&logoColor=white" alt="WhatsApp" height="28" /></a>
    <img src="https://komarev.com/ghpvc/?username=imeshsan2008&style=flat-square&color=cc0000&label=VIEWS" alt="Profile Views" height="28" />
  </p>
</div>

---

### `01` — About

Full-Stack Developer, Web & Graphic Designer based in **Kelaniya, Sri Lanka**, and Founder of **Vexora IT Solutions**. I design and ship scalable SaaS applications, privacy-first Chrome extensions, Python desktop utilities, and crisp visual systems — focused on clean architecture, speed, and zero visual clutter.

---

### `02` — Play Connect Four vs. AI *(Live Interactive Game)*

Challenge my automated **Depth-5 Minimax AI** directly from this README. Pick a column below, submit the pre-filled issue, and GitHub Actions will compute the AI counter-move and redraw the board automatically in ~15 seconds.

<!-- CONNECT4:START -->
<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/connect4-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="./assets/connect4-light.svg" />
    <img src="./assets/connect4-dark.svg" alt="Interactive Connect Four Board" width="100%" />
  </picture>
  <br /><br />
  <p>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:1&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+1.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-1.svg" alt="Drop Column 1" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:2&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+2.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-2.svg" alt="Drop Column 2" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:3&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+3.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-3.svg" alt="Drop Column 3" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:4&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+4.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-4.svg" alt="Drop Column 4" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:5&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+5.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-5.svg" alt="Drop Column 5" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:6&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+6.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-6.svg" alt="Drop Column 6" height="34" /></a>
  <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:drop:7&body=Click+%22Submit+new+issue%22+below+to+drop+your+piece+into+Column+7.+GitHub+Actions+will+run+the+Minimax+AI+and+update+the+README+board+in+~15+seconds%21"><img src="./assets/btn-col-7.svg" alt="Drop Column 7" height="34" /></a>
  </p>
  <p>
    <a href="https://github.com/imeshsan2008/imeshsan2008/issues/new?title=c4:new&body=Click+%22Submit+new+issue%22+below+to+reset+the+Connect+Four+board+and+start+a+fresh+match%21"><img src="./assets/btn-new.svg" alt="New Game" height="34" /></a>
  </p>
</div>
<!-- CONNECT4:END -->

<details>
<summary><strong>How to play &amp; engine specs</strong></summary>

1. Click any open column button (`▼ COL 01` – `▼ COL 07`) above.
2. On the pre-filled GitHub Issue page, click **Submit new issue** — no edits needed.
3. The [`connect4.yml`](./.github/workflows/connect4.yml) workflow executes [`scripts/connect4.py`](./scripts/connect4.py) with an **Alpha-Beta Minimax (Depth 5)** engine, updates [`game/state.json`](./game/state.json), re-renders both dark & light SVGs, replies with the move outcome, and closes the issue automatically.
4. Refresh this profile to see your crimson disc drop and the AI's counter-move. Anyone on GitHub can join the active match or click **↻ NEW GAME** to start a fresh round!

</details>

---

### `03` — Selected Builds

<table>
  <tr>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/imeshsan2008/MySLT_Tracker">MySLT Tracker</a></h4>
      <p>Open-source Chrome Manifest V3 extension &amp; Windows desktop widget to track SLT broadband usage, add-ons, and billing with 100% local storage and zero data collection.</p>
      <code>Chrome MV3</code> · <code>JavaScript</code> · <code>WPF</code>
    </td>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/imeshsan2008/AdobeShield">AdobeShield</a></h4>
      <p>Clean desktop utility built with Python &amp; ttkbootstrap to manage firewall rules and internet connectivity for Adobe Creative Cloud apps cleanly.</p>
      <code>Python</code> · <code>ttkbootstrap</code> · <code>Windows Firewall</code>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/imeshsan2008/Trainify">Trainify</a></h4>
      <p>Training management platform built to organize learning schedules, track skill development milestones, and manage tasks efficiently.</p>
      <code>Full-Stack</code> · <code>Web App</code> · <code>SaaS</code>
    </td>
    <td width="50%" valign="top">
      <h4><a href="https://github.com/imeshsan2008/ShareBox">ShareBox</a></h4>
      <p>Fast, offline peer-to-peer local file sharing over Wi-Fi hotspot — transfer files across devices with zero router or internet required.</p>
      <code>Python</code> · <code>Local Network</code> · <code>Utility</code>
    </td>
  </tr>
</table>

> **More systems:** [VenomQR Studio](https://github.com/imeshsan2008/qr) · [Magic Frame](https://github.com/imeshsan2008/magicframe) · [MediaX](https://github.com/imeshsan2008/mediax) · [Full Portfolio ↗](https://imeshsan2008.github.io/)

---

### `04` — GitHub Telemetry

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/stats-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="./assets/stats-light.svg" />
    <img src="./assets/stats-dark.svg" alt="GitHub Telemetry and Language Breakdown" width="100%" />
  </picture>
</div>

---

### `05` — Tech Stack & Capabilities

| Domain | Technologies & Tools |
| :--- | :--- |
| **Frontend & UI** | `HTML5` · `CSS3` · `JavaScript` · `Tailwind CSS` · `Bootstrap` · `Responsive Systems` |
| **Backend & Systems** | `Node.js` · `Python` · `PostgreSQL` · `REST APIs` · `MVC Architecture` · `Chrome MV3` |
| **Design & Visuals** | `UI/UX Design` · `Adobe Photoshop` · `Adobe Illustrator` · `Adobe Lightroom` · `CorelDRAW` |
| **Cloud & Tooling** | `DigitalOcean` · `Koyeb` · `Git` · `GitHub Actions` · `Production Linux` |

---

### `06` — Journey & Credentials

| Period | Role / Credential | Organization |
| :--- | :--- | :--- |
| **2026 — Present** | **Founder** — Full-Stack Web & SaaS Solutions | Vexora IT Solutions |
| **2025** | **Graphic Design Intern** — Branding, UI Assets & Layouts | National Productivity Secretariat |
| **2025** | **NVQ Level 4 — Graphic Design** | Maradana Technical College |
| **Certification** | **Professional Benchmarking** | Global Benchmarking Network |

---

### `07` — Contribution Snake

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/imeshsan2008/imeshsan2008/output/github-snake-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/imeshsan2008/imeshsan2008/output/github-snake-light.svg" />
    <img src="https://raw.githubusercontent.com/imeshsan2008/imeshsan2008/output/github-snake-dark.svg" alt="Contribution Snake Animation" width="100%" />
  </picture>
</div>

---

<div align="center">
  <sub>Built with crisp flat geometry — zero glow, 100% automated · <a href="https://imeshsan2008.github.io/">imeshsan2008.github.io</a></sub>
</div>
