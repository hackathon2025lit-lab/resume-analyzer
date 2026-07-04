// Dashboard: drag & drop upload, criteria weights, and analysis trigger.
(function () {
  const dropzone = document.getElementById('dropzone');
  if (!dropzone) return;

  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('browse-btn');
  const preview = document.getElementById('file-preview');
  const fpName = document.getElementById('fp-name');
  const fpSize = document.getElementById('fp-size');
  const removeBtn = document.getElementById('remove-file');
  const progressWrap = document.getElementById('progress-wrap');
  const progressFill = document.getElementById('progress-fill');
  const progressText = document.getElementById('progress-text');
  const uploadMsg = document.getElementById('upload-msg');
  const analyzeBtn = document.getElementById('analyze-btn');
  const analyzeMsg = document.getElementById('analyze-msg');
  const roleSelect = document.getElementById('job-role');
  const customRole = document.getElementById('custom-role');
  const deleteAfter = document.getElementById('delete-after');
  const weightTotalEl = document.getElementById('weight-total');

  const MAX_BYTES = 10 * 1024 * 1024;
  let currentResumeId = null;

  function human(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(2) + ' MB';
  }

  function setMsg(el, text, type) {
    el.textContent = text || '';
    el.className = 'inline-msg' + (type ? ' ' + type : '');
  }

  // ---- Criteria weights ----
  function updateWeightTotal() {
    let total = 0;
    document.querySelectorAll('.crit-slider').forEach((s) => {
      if (!s.disabled) total += parseInt(s.value || '0', 10);
    });
    weightTotalEl.textContent = total;
    weightTotalEl.parentElement.style.color = total === 100 ? 'var(--good)' : 'var(--muted)';
  }

  document.querySelectorAll('.criterion').forEach((row) => {
    const check = row.querySelector('.crit-check');
    const slider = row.querySelector('.crit-slider');
    const val = row.querySelector('.crit-val');
    check.addEventListener('change', () => {
      slider.disabled = !check.checked;
      if (!check.checked) { slider.value = 0; }
      else if (parseInt(slider.value, 10) === 0) { slider.value = 10; }
      val.textContent = slider.value + '%';
      updateWeightTotal();
    });
    slider.addEventListener('input', () => {
      val.textContent = slider.value + '%';
      updateWeightTotal();
    });
  });
  updateWeightTotal();

  function collectCriteria() {
    const criteria = {};
    document.querySelectorAll('.criterion').forEach((row) => {
      const check = row.querySelector('.crit-check');
      const slider = row.querySelector('.crit-slider');
      if (check.checked) criteria[slider.dataset.key] = parseInt(slider.value, 10);
    });
    return criteria;
  }

  // ---- Job role custom input ----
  roleSelect.addEventListener('change', () => {
    if (roleSelect.value === 'Custom Role') customRole.classList.remove('hidden');
    else customRole.classList.add('hidden');
  });

  // ---- File selection ----
  function validate(file) {
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx'].includes(ext)) return 'Invalid file type. Only PDF and DOCX are allowed.';
    if (file.size > MAX_BYTES) return 'File too large. Maximum size is 10 MB.';
    if (file.size === 0) return 'The file is empty.';
    return null;
  }

  function handleFile(file) {
    const err = validate(file);
    if (err) { setMsg(uploadMsg, err, 'error'); return; }
    fpName.textContent = file.name;
    fpSize.textContent = human(file.size);
    preview.classList.remove('hidden');
    setMsg(uploadMsg, '');
    uploadFile(file);
  }

  function uploadFile(file) {
    const form = new FormData();
    form.append('resume', file);
    progressWrap.classList.remove('hidden');
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    analyzeBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/resume/upload');
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        progressFill.style.width = pct + '%';
        progressText.textContent = pct + '%';
      }
    };
    xhr.onload = () => {
      let data = {};
      try { data = JSON.parse(xhr.responseText); } catch (e) {}
      if (xhr.status === 200 && data.ok) {
        currentResumeId = data.resume_id;
        progressFill.style.width = '100%';
        progressText.textContent = '100%';
        setMsg(uploadMsg, 'Uploaded and parsed: ' + (data.parsed.name || file.name), 'success');
        analyzeBtn.disabled = false;
      } else {
        setMsg(uploadMsg, (data && data.error) || 'Upload failed. Please try again.', 'error');
        progressWrap.classList.add('hidden');
      }
    };
    xhr.onerror = () => {
      setMsg(uploadMsg, 'Network error during upload. Please try again.', 'error');
      progressWrap.classList.add('hidden');
    };
    xhr.send(form);
  }

  browseBtn.addEventListener('click', () => fileInput.click());
  dropzone.addEventListener('click', (e) => { if (e.target === dropzone) fileInput.click(); });
  dropzone.addEventListener('keypress', (e) => { if (e.key === 'Enter') fileInput.click(); });
  fileInput.addEventListener('change', () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });

  ['dragenter', 'dragover'].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add('dragover'); }));
  ['dragleave', 'drop'].forEach((ev) =>
    dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); }));
  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
  });

  // ---- Remove file ----
  removeBtn.addEventListener('click', () => {
    if (currentResumeId) {
      fetch('/resume/' + currentResumeId, { method: 'DELETE' });
    }
    currentResumeId = null;
    fileInput.value = '';
    preview.classList.add('hidden');
    progressWrap.classList.add('hidden');
    analyzeBtn.disabled = true;
    setMsg(uploadMsg, 'File removed.', '');
  });

  // ---- Analyze ----
  analyzeBtn.addEventListener('click', () => {
    if (!currentResumeId) { setMsg(analyzeMsg, 'Please upload a resume first.', 'error'); return; }
    const label = analyzeBtn.querySelector('.btn-label');
    const spinner = analyzeBtn.querySelector('.spinner');
    analyzeBtn.disabled = true;
    label.textContent = 'Analyzing…';
    spinner.classList.remove('hidden');
    setMsg(analyzeMsg, '');

    fetch('/resume/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_id: currentResumeId,
        job_role: roleSelect.value,
        custom_role: customRole.value,
        criteria: collectCriteria(),
        delete_after: deleteAfter.checked,
      }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.ok && data.redirect) {
          window.location.href = data.redirect;
        } else {
          setMsg(analyzeMsg, data.error || 'Analysis failed. Please try again.', 'error');
          analyzeBtn.disabled = false;
          label.textContent = 'Analyze Resume';
          spinner.classList.add('hidden');
        }
      })
      .catch(() => {
        setMsg(analyzeMsg, 'Network error during analysis. Please try again.', 'error');
        analyzeBtn.disabled = false;
        label.textContent = 'Analyze Resume';
        spinner.classList.add('hidden');
      });
  });
})();
