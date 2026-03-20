# 🎂 HR Birthday Automator

An end-to-end, fully autonomous cloud pipeline that generates customized employee birthday graphics using AI background removal and delivers them directly to the company's social media team.

This project eliminates the manual graphic design and tracking process for HR and Marketing teams by connecting a live cloud database to a Python-based image generation script, orchestrated 24/7 via GitHub Actions.

## ⚙️ Architecture & Tech Stack
* Language: Python 3.10
* Database: Google Sheets API (`gspread`)
* AI Processing: `rembg` (u2net_human_seg model)
* Image Rendering: Pillow (PIL)
* Network & Delivery: `requests`, `smtplib` (SMTP SSL)
* CI/CD & Hosting: GitHub Actions (Cron scheduling)

## 🚀 Key Features
* Zero-Touch Automation: Runs dynamically at 6:00 AM PHT daily via a GitHub Actions scheduled workflow. No local hardware required.
* Intelligent Image Fetching: Processes headshots entirely in memory (`BytesIO`) from URLs, keeping the server lightweight.
* AI Human Segmentation: Utilizes advanced AI matting and post-processing masks to perfectly cut out employee headshots, even with complex backgrounds or lighting.
* Dynamic Graphical Templates: Automatically routes graphical assets, typography, and font stroke-widths based on employee variables.
* Secure Cloud Vault: All API keys and SMTP credentials are encrypted and injected at runtime via GitHub Secrets.

## 🛠️ Engineering Challenges Solved
* Google Drive Link Conversion: Implemented a RegEx (Regular Expression) interceptor that automatically converts standard Google Drive "Viewer" links pasted by HR into raw, direct-download image streams.
* Defensive Web Requests: Built HTTP header validation to ensure the bot gracefully skips rows if an invalid URL or non-image webpage is accidentally entered into the database.
* Edge-Case AI Artifacting: Separated the AI processing logic to use `alpha_matting` and `post_process_mask` differently based on the specific template structure to prevent "floating head" syndrome and edge bleeding.

---
*Developed by Florence Kyle D. Felices - IT Specialist*
