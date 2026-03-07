/* ════════════════════════════════════════════════════════════════
   CodeRefine AI – script.js
   Full frontend UI interaction, charts, and API logic
   ════════════════════════════════════════════════════════════════ */

/* Set marked.js options */
marked.setOptions({
    breaks: true,
    gfm: true,
});

/* DOM Elements */
const $ = id => document.getElementById(id);

// Sidebar Navigation
const navLinks = document.querySelectorAll('.nav-link');
const pageContents = document.querySelectorAll('.page-content');
const sidebarToggle = $('sidebar-toggle');
const sidebar = $('sidebar');

// Pages toggle logic
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        // Change link styles
        navLinks.forEach(l => {
            l.classList.remove('bg-blue-50', 'text-blue-600');
            l.querySelector('.sidebar-text')?.classList.remove('font-bold');
            if (l !== link) l.classList.add('text-slate-600', 'hover:text-slate-900', 'hover:bg-slate-50');
        });
        link.classList.remove('text-slate-600', 'hover:text-slate-900', 'hover:bg-slate-50');
        link.classList.add('bg-blue-50', 'text-blue-600');
        link.querySelector('.sidebar-text')?.classList.add('font-bold');

        // Toggle page content
        const target = link.getAttribute('data-target');
        pageContents.forEach(p => p.classList.remove('active'));
        const targetPage = $(`page-${target}`);
        if (targetPage) targetPage.classList.add('active');
    });
});

// Sidebar collapse Toggle
sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
});


/* ── Chart.js Setup ─────────────────────────────────────────── */
const ctx = document.getElementById('metricsChart').getContext('2d');
const gradient = ctx.createLinearGradient(0, 0, 0, 400);
gradient.addColorStop(0, 'rgba(124, 58, 237, 0.4)');
gradient.addColorStop(1, 'rgba(124, 58, 237, 0.05)');

const metricsChart = new Chart(ctx, {
    type: 'radar',
    data: {
        labels: ['Security', 'Code Quality', 'Performance', 'Best Practices', 'Dependencies'],
        datasets: [{
            label: 'System Score',
            data: [85, 78, 92, 80, 75],
            backgroundColor: gradient,
            borderColor: '#2563eb',
            pointBackgroundColor: '#fff',
            pointBorderColor: '#2563eb',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#2563eb',
            borderWidth: 2,
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            r: {
                angleLines: { color: 'rgba(0, 0, 0, 0.05)' },
                grid: { color: 'rgba(0, 0, 0, 0.1)' },
                pointLabels: {
                    color: '#64748b',
                    font: { size: 12, family: 'Inter', weight: '600' }
                },
                ticks: { display: false, min: 0, max: 100 }
            }
        },
        plugins: {
            legend: { display: false }
        }
    }
});


/* ── Utility Functions ───────────────────────────────────────── */
function showLoading(text) {
    $('loading-text').textContent = text;
    $('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    $('loading-overlay').classList.add('hidden');
}


/* ── Code Review Actions ─────────────────────────────────────── */
const loadDemoBtn = $('load-demo-btn');
const btnReview = $('btn-review');
const btnExplain = $('btn-explain');
const btnRewrite = $('btn-rewrite');

// Ace Editor Setup
let editor = null;
if ($('code-input')) {
    editor = ace.edit("code-input");
    editor.setTheme("ace/theme/chrome");
    editor.session.setMode("ace/mode/python");
    editor.setOptions({
        fontSize: "14px",
        showPrintMargin: false,
        wrap: true,
        useWorker: true // Enables built-in linters for JS/CSS/etc.
    });

    // Auto-check syntax on change for Python
    let syntaxCheckTimeout;
    editor.session.on('change', () => {
        clearTimeout(syntaxCheckTimeout);
        syntaxCheckTimeout = setTimeout(checkSyntax, 1000);
    });
}

const getLanguageMode = (lang) => {
    lang = lang.toLowerCase();
    if (lang === 'c++') return 'c_cpp';
    if (lang === 'typescript') return 'typescript';
    if (lang === 'javascript') return 'javascript';
    if (lang === 'java') return 'java';
    return 'python';
};

if ($('language-select')) {
    $('language-select').addEventListener('change', (e) => {
        if (editor) {
            editor.session.setMode("ace/mode/" + getLanguageMode(e.target.value));
            checkSyntax();
        }
    });
}

function getCodeValue() {
    return editor ? editor.getValue() : '';
}

let errorMarkers = [];

async function checkSyntax() {
    if (!editor) return;
    const code = editor.getValue();
    const language = $('language-select').value;

    // Clear previous UI errors and markers
    const errorDisplay = $('syntax-error-display');
    const errorText = $('syntax-error-text');
    if (errorDisplay) errorDisplay.classList.add('hidden');

    if (editor.session) {
        errorMarkers.forEach(m => editor.session.removeMarker(m));
        errorMarkers = [];
        editor.session.setAnnotations([]);
    }

    // Ace has built-in workers for Javascript/TypeScript, so we only need backend for Python
    if (language !== 'Python') return;

    if (!code.trim()) return;

    try {
        const res = await fetch('/api/check_syntax', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, language })
        });
        const data = await res.json();
        if (data.errors && data.errors.length > 0) {
            const Range = ace.require('ace/range').Range;
            const annotations = [];

            data.errors.forEach(err => {
                const row = err.line - 1;
                const col = err.column;

                annotations.push({
                    row: row,
                    column: col,
                    text: err.message,
                    type: "error"
                });

                // Add marker to highlight the issue line
                const range = new Range(row, 0, row, 100);
                const markerId = editor.session.addMarker(range, "ace_error-marker", "fullLine", false);
                errorMarkers.push(markerId);
            });

            editor.session.setAnnotations(annotations);

            // Show UI Banner
            if (errorDisplay && errorText) {
                const errInfo = data.errors[0];
                let infoHtml = '';
                if (errInfo.what && errInfo.improve && errInfo.correct) {
                    infoHtml = `
                    <div class="mt-2 ml-1 text-xs text-red-700 bg-red-100 p-3 rounded-lg flex flex-col gap-2">
                        <p><strong>🤔 What is the error?</strong><br/>${errInfo.what}</p>
                        <p><strong>💡 How to improve it:</strong><br/>${errInfo.improve}</p>
                        <p><strong>✅ How to correct it:</strong><br/>${errInfo.correct}</p>
                    </div>`;
                } else {
                    infoHtml = `<p class="mt-1">${errInfo.message}</p>`;
                }

                errorText.innerHTML = `<span class="font-bold text-red-800 text-base">🚨 Syntax Error at line ${errInfo.line}</span>${infoHtml}`;
                errorDisplay.classList.remove('hidden');
            }
        }
    } catch (err) {
        console.error("Syntax check error", err);
    }
}


// Sample Code loader
const DEMO_CODE = `function processPayment(userId, amt, callback) {
  var sql = "UPDATE users SET balance = balance - " + amt + " WHERE id = '" + userId + "'";
  db.execute(sql);
  // Do some heavy process synchronously
  for(var i=0; i<999999999; i++){}
  callback(true);
}`;
if (loadDemoBtn) {
    loadDemoBtn.addEventListener('click', () => {
        if (editor) {
            editor.setValue(DEMO_CODE, -1);
        }
        $('language-select').value = "JavaScript";
        if (editor) editor.session.setMode("ace/mode/javascript");
    });
}

// Markdown formatting helper
function decorateMarkdown(md) {
    let html = md.replace(/\[Critical\]/gi, "<span class='badge badge-critical'>Critical</span>");
    html = html.replace(/\[High\]/gi, "<span class='badge badge-high'>High</span>");
    html = html.replace(/\[Medium\]/gi, "<span class='badge badge-medium'>Medium</span>");
    html = html.replace(/\[Low\]/gi, "<span class='badge badge-low'>Low</span>");
    return html;
}

// 1. Review Code
if (btnReview) {
    btnReview.addEventListener('click', async () => {
        const code = getCodeValue().trim();
        if (!code) return alert("Please paste code to review.");

        const language = $('language-select').value;
        const focusElements = document.querySelectorAll('#page-code-review input[type="checkbox"]:checked');
        const focus_areas = Array.from(focusElements).map(cb => cb.value);

        showLoading("Detecting vulnerabilities & bugs...");

        try {
            const res = await fetch('/api/review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language, focus_areas })
            });
            const data = await res.json();

            if (!res.ok || data.detail) {
                const msg = data.detail || "Server error";
                alert("Review Failed: " + msg);
                return;
            }

            // Populate Original Code side
            $('review-orig-code').textContent = code;
            $('review-orig-code').className = `language-${language.toLowerCase()}`;
            hljs.highlightElement($('review-orig-code'));

            // Populate AI Review Report
            let mdContent = data.raw_response || "No response generated.";
            $('review-report').innerHTML = marked.parse(decorateMarkdown(mdContent));
            $('review-report').querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));

            $('review-results-view').classList.remove('hidden');

            // Send output to Security Report page
            fillSecurityReport(mdContent, "Security Review Results");

        } catch (err) {
            console.error(err);
            alert("Error running code review. Make sure server is running and Groq API key is set.");
        } finally {
            hideLoading();
        }
    });
}

// 2. Explain Code
if (btnExplain) {
    btnExplain.addEventListener('click', async () => {
        const code = getCodeValue().trim();
        if (!code) return alert("Please paste code to explain.");

        const language = $('language-select').value;

        showLoading("Generating code explanation...");

        try {
            const res = await fetch('/api/explain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            const data = await res.json();

            $('review-orig-code').textContent = code;
            $('review-orig-code').className = `language-${language.toLowerCase()}`;
            hljs.highlightElement($('review-orig-code'));

            const explMd = `### 💡 AI Explanation\n\n${data.explanation || "No explanation returned."}`;
            $('review-report').innerHTML = marked.parse(explMd);
            $('review-report').querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));

            $('review-results-view').classList.remove('hidden');

        } catch (err) {
            console.error(err);
            alert("Error explaining code.");
        } finally {
            hideLoading();
        }
    });
}

// 3. Fix & Rewrite
if (btnRewrite) {
    btnRewrite.addEventListener('click', async () => {
        const code = getCodeValue().trim();
        if (!code) return alert("Please paste code to rewrite.");

        const language = $('language-select').value;
        showLoading("Applying fixes & optimizations...");

        try {
            const res = await fetch('/api/rewrite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code, language })
            });
            const data = await res.json();

            $('rewrite-empty-state').classList.add('hidden');
            $('rewrite-results-view').classList.remove('hidden');

            $('rewrite-orig-code').textContent = code;
            $('rewrite-orig-code').className = `language-${language.toLowerCase()}`;
            hljs.highlightElement($('rewrite-orig-code'));

            let rwCode = data.rewritten_code;
            if (!rwCode && data.raw_response) {
                // Fallback if backend struct is different
                rwCode = data.raw_response.replace(/\`\`\`[a-z]*\n?/g, '').replace(/\`\`\`/g, '');
            }

            $('rewrite-new-code').textContent = rwCode || "// AI returned empty code";
            $('rewrite-new-code').className = `language-${language.toLowerCase()}`;
            hljs.highlightElement($('rewrite-new-code'));

            // Automatically switch to Code Rewrite page
            const rewriteNav = document.querySelector('[data-target="code-rewrite"]');
            if (rewriteNav) rewriteNav.click();

        } catch (err) {
            console.error(err);
            alert("Error rewriting code.");
        } finally {
            hideLoading();
        }
    });
}

// Copy Rewritten Code
const copyRwBtn = $('copy-rewritten-btn');
if (copyRwBtn) {
    copyRwBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText($('rewrite-new-code').textContent);
            copyRwBtn.textContent = "Copied!";
            copyRwBtn.classList.add('bg-emerald-500', 'text-white');
            setTimeout(() => {
                copyRwBtn.textContent = "Copy Rewritten Code";
                copyRwBtn.classList.remove('bg-emerald-500', 'text-white');
            }, 2000);
        } catch (e) {
            alert("Could not copy code");
        }
    });
}

// Copy Review Result
const copyReviewBtn = $('copy-review-content');
if (copyReviewBtn) {
    copyReviewBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText($('review-report').innerText);
            copyReviewBtn.textContent = "Copied!";
            setTimeout(() => { copyReviewBtn.textContent = "Copy"; }, 2000);
        } catch (e) { }
    });
}


/* ── GitHub Repository Analyzer ──────────────────────────────── */
const btnAnalyzeRepo = $('btn-analyze-repo');
if (btnAnalyzeRepo) {
    btnAnalyzeRepo.addEventListener('click', async () => {
        const url = $('github-url-input').value.trim();
        if (!url) return alert("Please enter a valid GitHub repository URL.");

        showLoading("Cloning & analyzing repository... This might take a minute.");

        try {
            const res = await fetch('/api/github-analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: url })
            });
            const data = await res.json();

            $('github-empty-state').classList.add('hidden');
            $('github-results-view').classList.remove('hidden');

            // Render Scores
            $('repo-sec-score').textContent = data.security_score || "N/A";
            $('repo-qual-score').textContent = data.quality_score || "N/A";

            const riskLvl = data.risk_level || "Medium";
            const riskEl = $('repo-risk-level');
            riskEl.textContent = riskLvl;

            // Adjust risk colors
            if (riskLvl === 'High') {
                riskEl.className = "text-3xl font-black text-red-600 uppercase mt-1";
                riskEl.parentElement.className = "bg-red-50 p-6 rounded-xl border border-red-200 text-center shadow-sm";
            } else if (riskLvl === 'Medium') {
                riskEl.className = "text-3xl font-black text-orange-600 uppercase mt-1";
                riskEl.parentElement.className = "bg-orange-50 p-6 rounded-xl border border-orange-200 text-center shadow-sm";
            } else {
                riskEl.className = "text-3xl font-black text-emerald-600 uppercase mt-1";
                riskEl.parentElement.className = "bg-emerald-50 p-6 rounded-xl border border-emerald-200 text-center shadow-sm";
            }

            // Fake extraction of risky files for display in the cards (In realities, we'd parse data.raw_response)
            const listObj = $('risky-files-list');
            listObj.innerHTML = `
               <li class="p-4 bg-slate-50 border border-slate-200 rounded-lg shadow-sm">
                   <div class="flex items-center gap-2 mb-1">
                     <span class="text-orange-600 font-bold whitespace-break-spaces break-all">⚠ Repository wide findings</span>
                   </div>
                   <p class="text-sm text-slate-500">See full Security Report for details.</p>
               </li>`;

            // Auto-populate the security report page
            let mdReport = data.raw_response || "No structural report found";
            fillSecurityReport(mdReport, `Analysis Report for: ${url}`);

            // Optional: Also update the dashboard chart to mirror the repo scores
            metricsChart.data.datasets[0].data = [
                parseInt(data.security_score) || 0,
                parseInt(data.quality_score) || 0,
                parseInt(data.performance_score) || 0,
                80, 70
            ];
            metricsChart.update();

        } catch (err) {
            console.error(err);
            alert("Failed to analyze repository.");
        } finally {
            hideLoading();
        }
    });
}


/* ── Security Report logic ──────────────────────────────────────*/
function fillSecurityReport(markdownData, titleString = "Detailed Security Breakdown") {
    $('security-empty-state').classList.add('hidden');
    $('security-results-view').classList.remove('hidden');

    const mdWrapped = `### ${titleString}\n\n${markdownData}`;

    // Inject the raw marked HTML
    $('security-issues-container').innerHTML = `
       <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm prose-slate prose w-full max-w-none">
           ${marked.parse(decorateMarkdown(mdWrapped))}
       </div>
    `;
    $('security-issues-container').querySelectorAll('pre code').forEach(block => hljs.highlightElement(block));
}


/* ── Init ────────────────────────────────────────────────────── */
// Ensure first page is active and colored
document.querySelector('[data-target="dashboard"]').click();
