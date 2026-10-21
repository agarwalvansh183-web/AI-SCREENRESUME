/**
 * ScreenAI — Frontend Application Logic
 * Manages UI interactions, screening engine requests, candidate pipelines, and analytics.
 */

// Global State
let currentJobs = [];
let selectedJob = null;
let currentCandidateId = null;
let selectedFile = null;
let inputMode = 'file'; // 'file' or 'text'
let searchDebounceTimeout = null;

// Pre-packaged realistic sample resumes for 1-click demo testing
const SAMPLE_RESUMES = {
  ai_lead: `Dr. Alex Sterling, Ph.D.
Email: alex.sterling.ai@example.com | Phone: (555) 382-9910 | Location: San Francisco, CA
LinkedIn: linkedin.com/in/alexsterling-ai | GitHub: github.com/asterling-ai

EXECUTIVE PROFILE:
Lead AI & Machine Learning Engineer with 6+ years of post-doctorate industry experience designing production LLMs, RAG pipelines, and scalable generative AI microservices. Expertise in deep learning frameworks, high-throughput model inference, and distributed training.

CORE TECHNICAL SKILLS:
- Languages & Frameworks: Python, PyTorch, TensorFlow, Keras, Scikit-Learn, Pandas, NumPy, C++
- AI / Generative AI: Large Language Models (LLMs), RAG, LangChain, Transformers, HuggingFace, NLP, Computer Vision, OpenCV, Vector DBs, ChromaDB, Pinecone
- Cloud & Infrastructure: FastAPI, Docker, Kubernetes, AWS (SageMaker, EC2, S3), CI/CD, Git, Linux
- Databases: PostgreSQL, SQL, Redis, MongoDB

PROFESSIONAL EXPERIENCE:
Senior AI Architect | Cerebro Tech (2021 - Present)
- Designed and deployed enterprise Generative AI agent workflows utilizing PyTorch, LangChain, and FastAPI serving 12M monthly queries.
- Optimized multi-node LLM fine-tuning pipelines using PyTorch FSDP on AWS GPU clusters, reducing training costs by 34%.
- Led a team of 5 ML engineers practicing Agile/Scrum delivery.

Machine Learning Engineer | Apex Cognitive Labs (2018 - 2021)
- Built computer vision and NLP classification models using TensorFlow and Scikit-Learn with 96.4% F1-score.
- Authored production REST APIs with FastAPI and containerized services using Docker and Kubernetes.

EDUCATION:
- Ph.D. in Computer Science (Artificial Intelligence) — Stanford University (2018)
- Bachelor of Science in Computer Science — UC Berkeley (2014)
`,

  fullstack: `Jordan Patel
Email: jordan.patel.dev@example.com | Phone: (555) 724-8192 | Austin, TX
Portfolio: jordanpatel.tech | GitHub: github.com/jpatel-fullstack

SUMMARY:
Senior Full Stack Python Developer with 4.5 years of experience building resilient cloud applications. Proficient in Python, FastAPI, Django, React, PostgreSQL, and modern DevOps tools.

KEY COMPETENCIES:
- Backend: Python, FastAPI, Django, REST APIs, Microservices, SQL, PostgreSQL, Redis
- Frontend: JavaScript, TypeScript, React, React.js, HTML5, CSS3, TailwindCSS
- DevOps & Tools: Docker, Git, CI/CD pipelines, AWS, Linux, Agile

EXPERIENCE:
Full Stack Software Engineer | Horizon Digital (2022 - Present)
- Architected core backend services using Python and FastAPI, handling 40,000 requests per minute with sub-50ms latency.
- Developed interactive web portals using React and modern JavaScript.
- Automated deployment workflows with Docker and GitHub Actions CI/CD.

Software Developer | CloudWave Solutions (2020 - 2022)
- Built scalable web apps with Django, PostgreSQL, and REST APIs.
- Collaborated in an agile scrum team to deliver multi-tenant SaaS features.

EDUCATION:
- B.Tech in Computer Science & Engineering — University of Texas (2020)
`,

  junior: `Samira Khan
Email: samira.khan.career@example.com | Phone: (555) 198-4421 | Chicago, IL

OBJECTIVE:
Enthusiastic Junior Developer seeking an entry-level software engineering role. Passionate about Python, web technologies, and problem solving.

SKILLS:
- Languages: Python, JavaScript, HTML, CSS, SQL (Basics)
- Tools: Git, VS Code, Linux

EXPERIENCE:
Junior Web Development Intern | TechStarts (2025 - Present)
- Assisted in maintaining internal web tools using basic Python scripts and HTML/CSS.
- Participated in weekly code reviews and bug fixes using Git.

EDUCATION:
- Bachelor of Science in Information Technology (Expected 2026)
`
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  setupNavigation();
  setupDropZone();
  loadJobs();
  loadEngineSettings();
  loadCandidates();
});

// ---------------- NAVIGATION & TABS ----------------

function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetTab = item.dataset.tab;
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  // Update sidebar active button
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.dataset.tab === tabId);
  });

  // Switch tab container
  document.querySelectorAll('.tab-view').forEach(view => {
    view.classList.toggle('active', view.id === `tab-${tabId}`);
  });

  // Update Header text
  const headings = {
    studio: { title: "AI Screening Studio", sub: "Evaluate candidate resumes against role requirements in real time" },
    candidates: { title: "Talent Pool & Candidates", sub: "Search, filter, inspect AI evaluation dossiers, and manage hiring pipeline" },
    jobs: { title: "Job Role Profiles", sub: "Manage role benchmarks and skill criteria used by the AI Screening Agent" },
    analytics: { title: "Screening Analytics & Intelligence", sub: "Macro-level applicant insights, match rates, and technical skill supply vs demand" },
    settings: { title: "AI Engine Configuration", sub: "Configure screening intelligence modes and Google Gemini LLM API keys" }
  };

  if (headings[tabId]) {
    document.getElementById('page-heading').textContent = headings[tabId].title;
    document.getElementById('page-subheading').textContent = headings[tabId].sub;
  }

  // Refresh data when switching to specific tabs
  if (tabId === 'candidates') loadCandidates();
  if (tabId === 'jobs') loadJobs();
  if (tabId === 'analytics') loadAnalytics();
  if (tabId === 'settings') loadEngineSettings();
}

// ---------------- JOBS MANAGEMENT ----------------

async function loadJobs() {
  try {
    const res = await fetch('/api/jobs');
    const jobs = await res.json();
    currentJobs = jobs;

    // Update job counts in sidebar
    document.getElementById('sidebar-job-count').textContent = jobs.length;

    // Populate Studio Dropdown
    const studioSelect = document.getElementById('studio-job-select');
    const candFilterJob = document.getElementById('cand-filter-job');

    studioSelect.innerHTML = '';
    candFilterJob.innerHTML = '<option value="">All Job Roles</option>';

    jobs.forEach((job, index) => {
      const opt = document.createElement('option');
      opt.value = job.id;
      opt.textContent = `${job.title} (${job.department})`;
      studioSelect.appendChild(opt);

      const filterOpt = document.createElement('option');
      filterOpt.value = job.id;
      filterOpt.textContent = job.title;
      candFilterJob.appendChild(filterOpt);
    });

    if (jobs.length > 0) {
      selectedJob = jobs[0];
      renderJobPreview(selectedJob);
    }

    renderJobsGrid(jobs);
  } catch (err) {
    showToast('Failed to load job listings', 'error');
  }
}

function onJobSelectionChange() {
  const select = document.getElementById('studio-job-select');
  const jobId = parseInt(select.value, 10);
  selectedJob = currentJobs.find(j => j.id === jobId) || null;
  if (selectedJob) {
    renderJobPreview(selectedJob);
  }
}

function renderJobPreview(job) {
  document.getElementById('preview-dept').textContent = job.department;
  document.getElementById('preview-exp').innerHTML = `<i class="fa-solid fa-clock"></i> ${job.min_experience_years}+ yrs exp`;

  const skillsContainer = document.getElementById('preview-skills');
  skillsContainer.innerHTML = '';

  (job.required_skills || []).forEach(skill => {
    const pill = document.createElement('span');
    pill.className = 'skill-pill match';
    pill.textContent = skill;
    skillsContainer.appendChild(pill);
  });

  (job.preferred_skills || []).forEach(skill => {
    const pill = document.createElement('span');
    pill.className = 'skill-pill neutral';
    pill.textContent = `+ ${skill}`;
    skillsContainer.appendChild(pill);
  });
}

function renderJobsGrid(jobs) {
  const grid = document.getElementById('jobs-cards-grid');
  grid.innerHTML = '';

  jobs.forEach(job => {
    const card = document.createElement('div');
    card.className = 'job-card';
    card.innerHTML = `
      <div class="job-card-top">
        <span class="job-card-dept">${escapeHtml(job.department)}</span>
        <span class="job-card-exp"><i class="fa-solid fa-clock"></i> ${job.min_experience_years}+ yrs</span>
      </div>
      <h3>${escapeHtml(job.title)}</h3>
      <p class="job-card-desc">${escapeHtml(job.description)}</p>
      <div class="job-card-skills">
        ${(job.required_skills || []).map(s => `<span class="skill-pill match">${escapeHtml(s)}</span>`).join('')}
      </div>
      <div class="job-card-footer">
        <span class="job-applicant-stat">
          <strong>${job.applicant_count || 0}</strong> Applicants (Avg: ${job.avg_score || 0}%)
        </span>
        <div style="display:flex; gap:6px;">
          <button class="btn btn-outline btn-xs" onclick="selectJobAndScreen(${job.id})">Screen for This Role</button>
          <button class="btn btn-outline btn-xs text-amber" title="Delete Role" onclick="deleteJobRole(${job.id})"><i class="fa-solid fa-trash"></i></button>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function selectJobAndScreen(jobId) {
  switchTab('studio');
  const select = document.getElementById('studio-job-select');
  select.value = jobId;
  onJobSelectionChange();
}

async function deleteJobRole(jobId) {
  if (!confirm("Are you sure you want to delete this job opening? Candidates associated with this job will also be removed.")) return;
  try {
    const res = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('Job role removed', 'success');
      loadJobs();
      loadCandidates();
    }
  } catch (e) {
    showToast('Failed to delete job', 'error');
  }
}

// ---------------- RESUME INPUT & DRAG/DROP ----------------

function setInputMode(mode) {
  inputMode = mode;
  document.getElementById('mode-file-btn').classList.toggle('active', mode === 'file');
  document.getElementById('mode-text-btn').classList.toggle('active', mode === 'text');
  document.getElementById('upload-zone-wrapper').classList.toggle('active', mode === 'file');
  document.getElementById('paste-zone-wrapper').classList.toggle('active', mode === 'text');
}

function setupDropZone() {
  const zone = document.getElementById('drop-zone');

  ['dragenter', 'dragover'].forEach(eventName => {
    zone.addEventListener(eventName, e => {
      e.preventDefault();
      zone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    zone.addEventListener(eventName, e => {
      e.preventDefault();
      zone.classList.remove('dragover');
    });
  });

  zone.addEventListener('drop', e => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      setFile(files[0]);
    }
  });
}

function handleFileSelected(event) {
  const file = event.target.files[0];
  if (file) {
    setFile(file);
  }
}

function setFile(file) {
  selectedFile = file;
  document.getElementById('selected-file-name').classList.remove('hidden');
  document.getElementById('file-name-text').textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
}

function clearSelectedFile() {
  selectedFile = null;
  document.getElementById('resume-file-input').value = '';
  document.getElementById('selected-file-name').classList.add('hidden');
}

function loadSampleResume(type) {
  setInputMode('text');
  const text = SAMPLE_RESUMES[type] || '';
  document.getElementById('resume-text-input').value = text;
  showToast(`Loaded ${type.toUpperCase()} sample resume into text area`, 'success');
}

// ---------------- RUN SCREENING AGENT ----------------

async function submitScreening() {
  if (!selectedJob) {
    showToast('Please select a target job position first', 'error');
    return;
  }

  const btn = document.getElementById('btn-run-screening');
  const emptyState = document.getElementById('result-empty-state');
  const loadingState = document.getElementById('result-loading-state');
  const activeView = document.getElementById('result-active-view');
  const stepText = document.getElementById('loading-step-text');

  // Validation
  if (inputMode === 'file' && !selectedFile) {
    // If no file uploaded, check if text area has content
    const pastedText = document.getElementById('resume-text-input').value.trim();
    if (pastedText) {
      inputMode = 'text';
    } else {
      showToast('Please upload a resume file or paste resume text', 'error');
      return;
    }
  }

  if (inputMode === 'text') {
    const pasted = document.getElementById('resume-text-input').value.trim();
    if (!pasted) {
      showToast('Please paste applicant resume text', 'error');
      return;
    }
  }

  // Show Loading Animation
  emptyState.classList.add('hidden');
  activeView.classList.add('hidden');
  loadingState.classList.remove('hidden');
  btn.disabled = true;

  // Animated loading step simulator
  const loadingSteps = [
    "Parsing applicant contact details & education...",
    "Building semantic skill taxonomy & verifying tech stack...",
    "Cross-referencing experience tenure against job benchmark...",
    "Synthesizing candidate strengths & uncovering skill gaps...",
    "Drafting tailored technical interview questions..."
  ];
  let stepIdx = 0;
  const stepInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % loadingSteps.length;
    stepText.textContent = loadingSteps[stepIdx];
  }, 450);

  try {
    let result = null;

    if (inputMode === 'file') {
      const formData = new FormData();
      formData.append('job_id', selectedJob.id);
      formData.append('file', selectedFile);

      const customName = document.getElementById('input-cand-name').value.trim();
      if (customName) formData.append('candidate_name', customName);

      const res = await fetch('/api/screen/upload', {
        method: 'POST',
        body: formData
      });
      result = await res.json();
    } else {
      const text = document.getElementById('resume-text-input').value.trim();
      const customName = document.getElementById('input-cand-name').value.trim();
      const customEmail = document.getElementById('input-cand-email').value.trim();

      const res = await fetch('/api/screen/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: selectedJob.id,
          resume_text: text,
          candidate_name: customName || undefined,
          email: customEmail || undefined
        })
      });
      result = await res.json();
    }

    clearInterval(stepInterval);

    if (result && result.success) {
      currentCandidateId = result.candidate_id;
      renderScreeningResult(result.candidate, result.evaluation);
      showToast(`Screening complete for ${result.candidate.candidate_name}!`, 'success');
      loadCandidates(); // Refresh candidate pool
      loadJobs(); // Refresh applicant counts
    } else {
      throw new Error(result ? result.detail || 'Evaluation failed' : 'Network error');
    }
  } catch (err) {
    clearInterval(stepInterval);
    showToast(`Screening error: ${err.message}`, 'error');
    emptyState.classList.remove('hidden');
  } finally {
    loadingState.classList.add('hidden');
    btn.disabled = false;
  }
}

function renderScreeningResult(cand, evalData) {
  const activeView = document.getElementById('result-active-view');
  activeView.classList.remove('hidden');

  // Candidate Header Details
  document.getElementById('res-candidate-name').textContent = cand.candidate_name;
  document.getElementById('res-email').innerHTML = `<i class="fa-solid fa-envelope"></i> ${cand.email || 'N/A'}`;
  document.getElementById('res-exp').innerHTML = `<i class="fa-solid fa-briefcase"></i> ${cand.experience_years} yrs exp`;
  document.getElementById('res-education').innerHTML = `<i class="fa-solid fa-graduation-cap"></i> ${cand.education || 'Degree not specified'}`;

  // Overall Score & Radial Progress
  const score = Math.round(evalData.overall_score);
  document.getElementById('res-overall-score').textContent = score;

  const circle = document.getElementById('score-circle-bar');
  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;
  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  const offset = circumference - (score / 100) * circumference;
  circle.style.strokeDashoffset = offset;

  // Radial color
  if (score >= 80) {
    circle.style.stroke = '#10b981';
  } else if (score >= 60) {
    circle.style.stroke = '#f59e0b';
  } else {
    circle.style.stroke = '#f43f5e';
  }

  // Recommendation Badge
  const verdictBadge = document.getElementById('res-recommendation-badge');
  verdictBadge.textContent = evalData.recommendation;
  verdictBadge.className = 'badge-verdict';
  if (evalData.recommendation === 'Strong Match') verdictBadge.classList.add('strong');
  else if (evalData.recommendation === 'Potential Match') verdictBadge.classList.add('potential');
  else verdictBadge.classList.add('weak');

  // Sub-scores
  document.getElementById('bar-skills-val').textContent = `${evalData.skills_score}%`;
  document.getElementById('bar-skills-fill').style.width = `${evalData.skills_score}%`;

  document.getElementById('bar-exp-val').textContent = `${evalData.experience_score}%`;
  document.getElementById('bar-exp-fill').style.width = `${evalData.experience_score}%`;

  document.getElementById('bar-edu-val').textContent = `${evalData.education_score}%`;
  document.getElementById('bar-edu-fill').style.width = `${evalData.education_score}%`;

  document.getElementById('bar-relevance-val').textContent = `${evalData.relevance_score}%`;
  document.getElementById('bar-relevance-fill').style.width = `${evalData.relevance_score}%`;

  // Summary
  document.getElementById('res-ai-summary').textContent = evalData.ai_summary;

  // Matched Skills
  const matchedContainer = document.getElementById('res-matched-skills');
  matchedContainer.innerHTML = '';
  (evalData.matched_skills || []).forEach(skill => {
    const pill = document.createElement('span');
    pill.className = 'skill-pill match';
    pill.textContent = skill;
    matchedContainer.appendChild(pill);
  });
  if (!evalData.matched_skills || evalData.matched_skills.length === 0) {
    matchedContainer.innerHTML = '<span class="skill-pill neutral">No direct skill matches</span>';
  }

  // Missing Skills
  const missingContainer = document.getElementById('res-missing-skills');
  missingContainer.innerHTML = '';
  (evalData.missing_skills || []).forEach(skill => {
    const pill = document.createElement('span');
    pill.className = 'skill-pill gap';
    pill.textContent = skill;
    missingContainer.appendChild(pill);
  });
  if (!evalData.missing_skills || evalData.missing_skills.length === 0) {
    missingContainer.innerHTML = '<span class="skill-pill match">All required skills present!</span>';
  }

  // Strengths List
  const strengthsList = document.getElementById('res-strengths-list');
  strengthsList.innerHTML = '';
  (evalData.strengths || []).forEach(s => {
    const li = document.createElement('li');
    li.textContent = s;
    strengthsList.appendChild(li);
  });

  // Weaknesses List
  const weakList = document.getElementById('res-weaknesses-list');
  weakList.innerHTML = '';
  (evalData.weaknesses || []).forEach(w => {
    const li = document.createElement('li');
    li.textContent = w;
    weakList.appendChild(li);
  });

  // Tailored Interview Questions
  const questionsContainer = document.getElementById('res-questions-container');
  questionsContainer.innerHTML = '';
  (evalData.interview_questions || []).forEach(q => {
    const item = document.createElement('div');
    item.className = 'question-item';
    item.innerHTML = `
      <div class="question-category">${escapeHtml(q.category || 'Interview Question')}</div>
      <div class="question-text">${escapeHtml(q.question)}</div>
      <div class="eval-guide">Evaluation Focus: ${escapeHtml(q.eval_guide || '')}</div>
    `;
    questionsContainer.appendChild(item);
  });

  // Update status select initial value
  const statusSelect = document.getElementById('res-change-status-select');
  if (score >= 80) statusSelect.value = 'Shortlisted';
  else if (score < 50) statusSelect.value = 'Rejected';
  else statusSelect.value = 'Under Review';
}

async function updateCurrentCandidateStatus() {
  if (!currentCandidateId) return;
  const select = document.getElementById('res-change-status-select');
  const newStatus = select.value;

  try {
    const res = await fetch(`/api/candidates/${currentCandidateId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      showToast(`Status updated to "${newStatus}"`, 'success');
      loadCandidates();
    }
  } catch (e) {
    showToast('Failed to update status', 'error');
  }
}

// ---------------- TALENT POOL / CANDIDATES ----------------

async function loadCandidates() {
  try {
    const jobFilter = document.getElementById('cand-filter-job').value;
    const statusFilter = document.getElementById('cand-filter-status').value;
    const searchVal = document.getElementById('cand-search-input').value.trim();

    let url = '/api/candidates?';
    if (jobFilter) url += `job_id=${jobFilter}&`;
    if (statusFilter && statusFilter !== 'All') url += `status=${encodeURIComponent(statusFilter)}&`;
    if (searchVal) url += `search=${encodeURIComponent(searchVal)}&`;

    const res = await fetch(url);
    const candidates = await res.json();

    document.getElementById('sidebar-candidate-count').textContent = candidates.length;
    renderCandidatesTable(candidates);
  } catch (err) {
    showToast('Failed to load candidate list', 'error');
  }
}

function debounceFilterCandidates() {
  clearTimeout(searchDebounceTimeout);
  searchDebounceTimeout = setTimeout(() => {
    loadCandidates();
  }, 250);
}

function renderCandidatesTable(candidates) {
  const tbody = document.getElementById('candidates-table-body');
  const emptyMsg = document.getElementById('candidates-empty-msg');
  tbody.innerHTML = '';

  if (candidates.length === 0) {
    emptyMsg.classList.remove('hidden');
    return;
  }
  emptyMsg.classList.add('hidden');

  candidates.forEach(c => {
    const tr = document.createElement('tr');

    const score = Math.round(c.overall_score || 0);
    let scoreColor = '#10b981';
    if (score < 60) scoreColor = '#f43f5e';
    else if (score < 80) scoreColor = '#f59e0b';

    let statusClass = 'review';
    if (c.status === 'Shortlisted') statusClass = 'shortlisted';
    else if (c.status === 'Interview Scheduled') statusClass = 'interview';
    else if (c.status === 'Rejected') statusClass = 'rejected';

    tr.innerHTML = `
      <td class="cand-name-cell">
        <strong>${escapeHtml(c.candidate_name)}</strong>
        <span>${escapeHtml(c.email || 'N/A')}</span>
      </td>
      <td>${escapeHtml(c.job_title || 'N/A')}</td>
      <td>
        <span class="score-badge-table" style="color: ${scoreColor};">${score}%</span>
      </td>
      <td>
        <span class="badge-verdict ${c.recommendation === 'Strong Match' ? 'strong' : c.recommendation === 'Potential Match' ? 'potential' : 'weak'}" style="font-size: 11px;">
          ${escapeHtml(c.recommendation || 'N/A')}
        </span>
      </td>
      <td>
        <span class="status-pill ${statusClass}">${escapeHtml(c.status || 'Under Review')}</span>
      </td>
      <td style="color: var(--text-dim); font-size: 12px;">${(c.created_at || '').substring(0, 10)}</td>
      <td>
        <button class="btn btn-outline btn-xs" onclick="openCandidateDossier(${c.id})">
          <i class="fa-solid fa-file-magnifying-glass"></i> Full Dossier
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// ---------------- CANDIDATE DOSSIER MODAL ----------------

let modalCandidateId = null;

async function openCandidateDossier(candidateId) {
  try {
    const res = await fetch(`/api/candidates/${candidateId}`);
    if (!res.ok) throw new Error('Candidate not found');
    const cand = await res.json();
    modalCandidateId = cand.id;

    document.getElementById('modal-cand-name').textContent = cand.candidate_name;
    document.getElementById('modal-cand-meta').textContent = `${cand.email || 'No email'} • ${cand.experience_years} yrs exp • Applied for: ${cand.job_title}`;

    document.getElementById('modal-score-overall').textContent = `${Math.round(cand.overall_score || 0)}%`;
    document.getElementById('modal-score-skills').textContent = `${Math.round(cand.skills_score || 0)}%`;
    document.getElementById('modal-score-exp').textContent = `${Math.round(cand.experience_score || 0)}%`;
    document.getElementById('modal-score-relevance').textContent = `${Math.round(cand.relevance_score || 0)}%`;

    document.getElementById('modal-summary-text').textContent = cand.ai_summary || 'No summary available.';

    // Matched skills
    const matchBox = document.getElementById('modal-matched-skills');
    matchBox.innerHTML = '';
    (cand.matched_skills || []).forEach(s => {
      const p = document.createElement('span');
      p.className = 'skill-pill match';
      p.textContent = s;
      matchBox.appendChild(p);
    });

    // Missing skills
    const missBox = document.getElementById('modal-missing-skills');
    missBox.innerHTML = '';
    (cand.missing_skills || []).forEach(s => {
      const p = document.createElement('span');
      p.className = 'skill-pill gap';
      p.textContent = s;
      missBox.appendChild(p);
    });

    // Interview Questions
    const qList = document.getElementById('modal-interview-questions');
    qList.innerHTML = '';
    (cand.interview_questions || []).forEach(q => {
      const item = document.createElement('div');
      item.className = 'question-item';
      item.innerHTML = `
        <div class="question-category">${escapeHtml(q.category || 'Interview Question')}</div>
        <div class="question-text">${escapeHtml(q.question)}</div>
        <div class="eval-guide">Evaluation Focus: ${escapeHtml(q.eval_guide || '')}</div>
      `;
      qList.appendChild(item);
    });

    // Recruiter status & notes
    document.getElementById('modal-status-select').value = cand.status || 'Under Review';
    document.getElementById('modal-notes-input').value = cand.notes || '';

    document.getElementById('dossier-modal').classList.remove('hidden');
  } catch (err) {
    showToast('Failed to load candidate dossier', 'error');
  }
}

function closeDossierModal() {
  document.getElementById('dossier-modal').classList.add('hidden');
  modalCandidateId = null;
}

async function saveModalCandidateStatus() {
  if (!modalCandidateId) return;
  const status = document.getElementById('modal-status-select').value;
  const notes = document.getElementById('modal-notes-input').value.trim();

  try {
    const res = await fetch(`/api/candidates/${modalCandidateId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, notes })
    });
    if (res.ok) {
      showToast('Candidate status and notes saved', 'success');
      closeDossierModal();
      loadCandidates();
    }
  } catch (e) {
    showToast('Error saving changes', 'error');
  }
}

// ---------------- NEW JOB MODAL ----------------

function openNewJobModal() {
  document.getElementById('job-modal').classList.remove('hidden');
}

function closeNewJobModal() {
  document.getElementById('job-modal').classList.add('hidden');
}

async function submitNewJob() {
  const title = document.getElementById('new-job-title').value.trim();
  const dept = document.getElementById('new-job-dept').value.trim();
  const exp = parseInt(document.getElementById('new-job-exp').value, 10) || 0;
  const reqSkillsRaw = document.getElementById('new-job-req-skills').value.trim();
  const prefSkillsRaw = document.getElementById('new-job-pref-skills').value.trim();
  const desc = document.getElementById('new-job-desc').value.trim();

  if (!title || !dept || !reqSkillsRaw || !desc) {
    showToast('Please fill in all required job fields', 'error');
    return;
  }

  const required_skills = reqSkillsRaw.split(',').map(s => s.trim()).filter(Boolean);
  const preferred_skills = prefSkillsRaw.split(',').map(s => s.trim()).filter(Boolean);

  try {
    const res = await fetch('/api/jobs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        department: dept,
        experience_level: `${exp}+ yrs`,
        min_experience_years: exp,
        required_skills,
        preferred_skills,
        description: desc
      })
    });

    if (res.ok) {
      showToast(`Job role "${title}" created!`, 'success');
      closeNewJobModal();
      loadJobs();
    } else {
      showToast('Failed to create job', 'error');
    }
  } catch (err) {
    showToast('Error creating job opening', 'error');
  }
}

// ---------------- ANALYTICS ----------------

async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();

    document.getElementById('metric-total-screened').textContent = data.total_screened || 0;
    document.getElementById('metric-shortlisted').textContent = data.shortlisted || 0;
    document.getElementById('metric-interviews').textContent = data.interview_scheduled || 0;
    document.getElementById('metric-avg-score').textContent = `${data.avg_match_score || 0}%`;

    // Render top matched skills
    const matchedList = document.getElementById('stat-matched-skills-list');
    matchedList.innerHTML = '';
    const topMatched = data.top_matched_skills || [];
    const maxMatchCount = Math.max(...topMatched.map(s => s.count), 1);

    topMatched.forEach(item => {
      const pct = Math.round((item.count / maxMatchCount) * 100);
      const row = document.createElement('div');
      row.className = 'stat-row';
      row.innerHTML = `
        <span class="stat-name">${escapeHtml(item.skill)}</span>
        <div class="stat-bar-track">
          <div class="stat-bar-fill emerald" style="width: ${pct}%;"></div>
        </div>
        <span class="stat-count">${item.count}</span>
      `;
      matchedList.appendChild(row);
    });
    if (topMatched.length === 0) {
      matchedList.innerHTML = '<p style="color:var(--text-dim); font-size:13px;">No skill metrics recorded yet.</p>';
    }

    // Render top missing skills
    const missingList = document.getElementById('stat-missing-skills-list');
    missingList.innerHTML = '';
    const topMissing = data.top_missing_skills || [];
    const maxMissCount = Math.max(...topMissing.map(s => s.count), 1);

    topMissing.forEach(item => {
      const pct = Math.round((item.count / maxMissCount) * 100);
      const row = document.createElement('div');
      row.className = 'stat-row';
      row.innerHTML = `
        <span class="stat-name">${escapeHtml(item.skill)}</span>
        <div class="stat-bar-track">
          <div class="stat-bar-fill amber" style="width: ${pct}%;"></div>
        </div>
        <span class="stat-count">${item.count}</span>
      `;
      missingList.appendChild(row);
    });
    if (topMissing.length === 0) {
      missingList.innerHTML = '<p style="color:var(--text-dim); font-size:13px;">No missing skill bottlenecks found yet.</p>';
    }
  } catch (e) {
    showToast('Failed to load analytics', 'error');
  }
}

// ---------------- EXPORT ----------------

function exportCandidatesCSV() {
  const jobFilter = document.getElementById('cand-filter-job')?.value || '';
  let url = '/api/export/csv';
  if (jobFilter) url += `?job_id=${jobFilter}`;
  window.open(url, '_blank');
}

// ---------------- SETTINGS & ENGINE CONFIG ----------------

// Tracks the manually forced mode ('local' | 'gemini' | null = auto)
let forcedEngineMode = localStorage.getItem('forcedEngineMode') || null;

async function loadEngineSettings() {
  try {
    const res = await fetch('/api/settings');
    const settings = await res.json();

    const hasKey = settings.has_gemini_key;

    // Determine effective mode
    let activeMode;
    if (forcedEngineMode === 'local') {
      activeMode = 'local';
    } else if (forcedEngineMode === 'gemini' && hasKey) {
      activeMode = 'gemini';
    } else {
      activeMode = hasKey ? 'gemini' : 'local';
    }

    // Update engine cards
    const localCard = document.getElementById('engine-card-local');
    const geminiCard = document.getElementById('engine-card-gemini');
    const localBadge = document.getElementById('engine-badge-local');
    const geminiBadge = document.getElementById('engine-badge-gemini');
    const clearBtn = document.getElementById('btn-clear-key');

    if (localCard && geminiCard) {
      localCard.classList.toggle('active', activeMode === 'local');
      geminiCard.classList.toggle('active', activeMode === 'gemini');
      localBadge.textContent = activeMode === 'local' ? 'Active Engine' : 'Click to Activate';
      geminiBadge.textContent = activeMode === 'gemini' ? 'Active Engine' : (hasKey ? 'Click to Activate' : 'Requires API Key');
    }

    // Show/hide Clear Key button
    if (clearBtn) clearBtn.style.display = hasKey ? 'inline-flex' : 'none';

    // Update sidebar status indicator
    const engineNameEl = document.getElementById('status-engine-name');
    const engineDescEl = document.getElementById('status-engine-desc');
    if (activeMode === 'gemini') {
      engineNameEl.textContent = 'Gemini 2.5 Flash LLM';
      engineNameEl.style.color = 'var(--accent-cyan)';
      engineDescEl.textContent = `API Key: ${settings.masked_key}`;
    } else {
      engineNameEl.textContent = 'Local NLP Agent';
      engineNameEl.style.color = 'var(--accent-emerald)';
      engineDescEl.textContent = 'High-Precision Semantic Parser';
    }
  } catch (e) {
    console.error(e);
  }
}

async function selectEngineMode(mode) {
  try {
    const res = await fetch('/api/settings');
    const settings = await res.json();

    if (mode === 'gemini' && !settings.has_gemini_key) {
      showToast('⚠️ Please save a Gemini API key first to use this engine.', 'error');
      // Scroll key input into view
      document.getElementById('settings-gemini-key')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.getElementById('settings-gemini-key')?.focus();
      return;
    }

    forcedEngineMode = mode;
    localStorage.setItem('forcedEngineMode', mode);

    // Persist selection to backend
    await fetch('/api/settings/set-mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });

    await loadEngineSettings();
    showToast(
      mode === 'gemini'
        ? '🤖 Switched to Google Gemini 2.5 Flash LLM engine'
        : '⚡ Switched to Local High-Precision NLP engine',
      'success'
    );
  } catch (e) {
    showToast('Failed to switch engine mode', 'error');
  }
}


async function saveGeminiApiKey() {
  const keyInput = document.getElementById('settings-gemini-key');
  const key = keyInput.value.trim();

  if (!key) {
    showToast('Please enter a Gemini API key before saving.', 'error');
    return;
  }

  try {
    const res = await fetch('/api/settings/save-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: key })
    });
    if (res.ok) {
      showToast('✅ Gemini API key saved! Switching to Gemini engine.', 'success');
      keyInput.value = '';
      // Auto-select Gemini when a key is saved
      forcedEngineMode = 'gemini';
      localStorage.setItem('forcedEngineMode', 'gemini');
      await fetch('/api/settings/set-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'gemini' })
      });
      loadEngineSettings();
    }
  } catch (err) {
    showToast('Failed to save API key', 'error');
  }
}

async function clearGeminiApiKey() {
  try {
    const res = await fetch('/api/settings/save-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ api_key: '' })
    });
    if (res.ok) {
      forcedEngineMode = 'local';
      localStorage.setItem('forcedEngineMode', 'local');
      await fetch('/api/settings/set-mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'local' })
      });
      showToast('🗑️ API key cleared. Reverted to Local NLP engine.', 'success');
      loadEngineSettings();
    }
  } catch (err) {
    showToast('Failed to clear API key', 'error');
  }
}

// ---------------- TOAST NOTIFICATIONS & UTILS ----------------

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = type === 'success' ? 'fa-circle-check text-emerald' : type === 'error' ? 'fa-triangle-exclamation text-amber' : 'fa-info-circle';
  toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
