// index.js - Main JavaScript for the index page

document.addEventListener('DOMContentLoaded', function() {
  // Elements
  const dropArea = document.querySelector('.file-drop-area');
  const fileInput = document.getElementById('file-input');
  const fileDetails = document.getElementById('file-details');
  const uploadForm = document.getElementById('upload-form');
  const generateBtn = document.getElementById('generate-btn');
  const loadingOverlay = document.getElementById('loading-overlay');
  const loadingBar = document.getElementById('loading-bar');
  const loadingPercentage = document.getElementById('loading-percentage');
  const loadingComplete = document.getElementById('loading-complete');
  const viewDocLink = document.getElementById('view-doc-link');
  const githubUrlInput = document.getElementById('github-url');
  
  // Tab functionality
  const tabButtons = document.querySelectorAll('.tab-btn');
  const tabContents = document.querySelectorAll('.tab-content');
  
  tabButtons.forEach(button => {
    button.addEventListener('click', function() {
      // Remove active class from all buttons and contents
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      
      // Add active class to clicked button
      this.classList.add('active');
      
      // Show corresponding content
      const tabId = this.getAttribute('data-tab');
      document.getElementById(tabId + '-tab').classList.add('active');
    });
  });
  
  // Organization selection for visibility
  const visibilityRadios = document.querySelectorAll('input[name="visibility"]');
  const orgSelectWrapper = document.getElementById('org-select-wrapper');
  
  if (visibilityRadios && orgSelectWrapper) {
    visibilityRadios.forEach(radio => {
      radio.addEventListener('change', function() {
        if (this.value === 'organization') {
          orgSelectWrapper.style.display = 'block';
        } else {
          orgSelectWrapper.style.display = 'none';
        }
      });
    });
  }
  
  // Prevent default behavior for drag events
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
  });
  
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }
  
  // Highlight drop area when dragging file over it
  ['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
  });
  
  function highlight() {
    dropArea.classList.add('is-active');
  }
  
  function unhighlight() {
    dropArea.classList.remove('is-active');
  }
  
  // Handle file drop
  dropArea.addEventListener('drop', handleDrop, false);
  
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;
    updateFileDetails();
  }
  
  // Update file details when file is selected via input
  fileInput.addEventListener('change', updateFileDetails);
  
  function updateFileDetails() {
    if (fileInput.files && fileInput.files[0]) {
      const file = fileInput.files[0];
      // Format file size
      const fileSize = (file.size / 1024).toFixed(2) + ' KB';
      fileDetails.innerHTML = `<strong>${file.name}</strong> (${fileSize})`;
      fileDetails.classList.add('has-file');
      
      // Clear GitHub URL input when file is selected
      if (githubUrlInput) {
        githubUrlInput.value = '';
      }
    } else {
      fileDetails.innerHTML = '';
      fileDetails.classList.remove('has-file');
    }
  }
  
  // Clear file input when GitHub URL is entered
  if (githubUrlInput) {
    githubUrlInput.addEventListener('input', function() {
      if (this.value.trim() !== '') {
        // Clear file input and details
        fileInput.value = '';
        fileDetails.innerHTML = '';
        fileDetails.classList.remove('has-file');
      }
    });
  }
  
  // Clear GitHub URL input when file is selected
  fileInput.addEventListener('change', function() {
    if (fileInput.files && fileInput.files[0] && githubUrlInput) {
      githubUrlInput.value = '';
    }
  });
  
  // Handle form submission and show loading overlay
  uploadForm.addEventListener('submit', function(e) {
    // Check if either file is selected or GitHub URL is provided
    const hasFile = fileInput.files && fileInput.files[0];
    const hasGithubUrl = githubUrlInput && githubUrlInput.value.trim() !== '';
    
    if (hasFile || hasGithubUrl) {
      e.preventDefault();
      
      // First submit the form silently
      const formData = new FormData(uploadForm);
      
      // Show loading overlay
      loadingOverlay.style.display = 'flex';
      
      // Simulate loading progress
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 3;
        if (progress > 95) progress = 95; // Stop at 95% until completion
        
        loadingBar.style.width = progress + '%';
        loadingPercentage.textContent = Math.round(progress) + '%';
      }, 200);
      
      // Submit the form in the background
      fetch(uploadForm.action || window.location.href, {
        method: 'POST',
        body: formData
      })
      .then(response => response.text())
      .then(html => {
        // Parsing completed - set to 100%
        clearInterval(interval);
        progress = 100;
        loadingBar.style.width = '100%';
        loadingPercentage.textContent = '100%';
        
        // Parse the response to get the ID of the generated doc
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Try to get latest doc ID from the response
        const latestDocIdEl = doc.getElementById('latest-doc-id');
        if (latestDocIdEl) {
          const latestDocId = latestDocIdEl.value;
          viewDocLink.setAttribute('href', `/doc_view/view/${latestDocId}/`);
        } else {
          // Fallback to first doc in the list
          const docLinks = doc.querySelectorAll('.doc-link');
          if (docLinks.length > 0) {
            const latestDocLink = docLinks[0].getAttribute('href');
            viewDocLink.setAttribute('href', latestDocLink);
          }
        }
        
        // Show completion message
        loadingComplete.style.display = 'block';
      })
      .catch(error => {
        console.error('Error submitting form:', error);
        clearInterval(interval);
        loadingPercentage.textContent = 'Error';
        // Allow form to submit normally if fetch fails
        uploadForm.submit();
      });
    }
  });
  
  // Close overlay when close button is clicked
  document.getElementById('close-overlay-btn').addEventListener('click', function() {
    loadingOverlay.style.display = 'none';
  });
});