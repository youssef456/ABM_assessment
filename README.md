# Technical Assessment - Automation, Interception, Scraping, and System Design

This repository contains the implementation for a four-part technical assessment focusing on stealth automation, network interception, data scraping, and system architecture.

## Project Structure

- `task_1_automation.py`: Stealth automation using Playwright to solve Cloudflare Turnstile captchas.
- `task_2_interception.py`: Network interception script that blocks Turnstile loading.
- `task_3_scraping.py`: DOM scraping assessment capturing images and text.
- `prompt_task_1.txt`, `prompt_task_2.txt`, `prompt_task_3.txt`: The AI prompts used to generate the logic for each task.
- `task_4_diagram/`: Contains the architecture diagram and a detailed technical explanation.
- `videos/`: Contains descriptive recordings: `Task_1_Consolidated.webm` (All 10 trials) and `Task_2_Interception.webm`.
- `allimages.json` / `visible_images_only.json`: (Generated) Results from the scraping task.

## Approach

### Task 1: Stealth Automation
Implemented using **Playwright** with the `playwright-stealth` library. The script navigates to the target Turnstile page, simulates human-like interaction by clicking the widget based on coordinate observations, and waits for the dynamically generated response token. Results are logged with a focus on attaining a >60% success rate across 10 trials.

### Task 2: Network Interception
Utilizes Playwright's `page.route` to intercept and abort requests to `challenges.cloudflare.com`. This demonstrates the ability to block captcha loading while extracting critical metadata from the network traffic and successfully injecting a pre-obtained token to pass verification.

### Task 3: DOM Scraping
Uses JavaScript execution within the browser context to identify image elements. It differentiate between "all images" and "visible images" by checking computed styles (display, visibility) and viewport bounding boxes. All images are converted to base64 via a canvas-based extraction method.

### Task 4: System Architecture
Designed a robust, scalable backend using **RabbitMQ** for task distribution, horizontally scalable **Worker Nodes** for processing, and a secondary **SQL Failover** system. Monitoring is integrated using a Prometheus/ELK stack for health and error tracking.

## Usage

### Prerequisites
- Python 3.10+
- Playwright

```bash
pip install playwright playwright-stealth
playwright install chromium
```

### Running Tasks
```bash
# Task 1
python task_1_automation.py

# Task 2
python task_2_interception.py

# Task 3
python task_3_scraping.py
```

## Results & Delivery
- Videos for Task 1 and 2 are stored in the `videos/` directory with descriptive names.
- AI Prompts for Tasks 1, 2, and 3 are included as requested.
- Scraping results are in `allimages.json` and `visible_images_only.json`.
- Success rate for Task 1 is logged to the console and `task_1_results.json`.
