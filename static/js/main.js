// Mobile Menu Toggle
const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
const closeMenuBtn = document.querySelector('.close-menu-btn');
const mobileMenu = document.querySelector('.mobile-menu');

if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.add('active');
        document.body.style.overflow = 'hidden';
    });
    
    closeMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.remove('active');
        document.body.style.overflow = '';
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!mobileMenu.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
            mobileMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}

// Close flash messages
document.querySelectorAll('.flash-close').forEach(button => {
    button.addEventListener('click', (e) => {
        e.target.closest('.flash-message').remove();
    });
});

// Auto-hide flash messages after 5 seconds
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(message => {
        message.style.opacity = '0';
        setTimeout(() => message.remove(), 300);
    });
}, 5000);

// Like functionality
document.querySelectorAll('.like-btn').forEach(button => {
    button.addEventListener('click', async function() {
        const postId = this.dataset.postId;
        const isLiked = this.classList.contains('liked');
        
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
            const response = await fetch(`/post/${postId}/like`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                credentials: 'same-origin'
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Update button state
                if (data.liked) {
                    this.classList.add('liked');
                    this.innerHTML = `<i class="fas fa-heart"></i> Liked (${data.like_count})`;
                } else {
                    this.classList.remove('liked');
                    this.innerHTML = `<i class="far fa-heart"></i> Like (${data.like_count})`;
                }
            }
        } catch (error) {
            console.error('Error liking post:', error);
        }
    });
});

// Rich text editor for blog content
document.addEventListener('DOMContentLoaded', function() {
    const contentEditor = document.getElementById('content');
    
    if (contentEditor) {
        // Create toolbar
        const toolbar = document.createElement('div');
        toolbar.className = 'editor-toolbar';
        toolbar.innerHTML = `
            <button type="button" data-command="bold"><i class="fas fa-bold"></i></button>
            <button type="button" data-command="italic"><i class="fas fa-italic"></i></button>
            <button type="button" data-command="underline"><i class="fas fa-underline"></i></button>
            <button type="button" data-command="insertUnorderedList"><i class="fas fa-list-ul"></i></button>
            <button type="button" data-command="insertOrderedList"><i class="fas fa-list-ol"></i></button>
            <button type="button" data-command="createLink"><i class="fas fa-link"></i></button>
            <button type="button" data-command="unlink"><i class="fas fa-unlink"></i></button>
            <button type="button" data-command="formatBlock" data-value="h2">H2</button>
            <button type="button" data-command="formatBlock" data-value="h3">H3</button>
            <button type="button" data-command="formatBlock" data-value="p">P</button>
        `;
        
        // Insert toolbar before textarea
        contentEditor.parentNode.insertBefore(toolbar, contentEditor);
        
        // Add toolbar functionality
        toolbar.addEventListener('click', function(e) {
            if (e.target.tagName === 'BUTTON' || e.target.parentElement.tagName === 'BUTTON') {
                e.preventDefault();
                const button = e.target.tagName === 'BUTTON' ? e.target : e.target.parentElement;
                const command = button.dataset.command;
                const value = button.dataset.value;
                
                contentEditor.focus();
                
                if (command === 'createLink') {
                    const url = prompt('Enter URL:');
                    if (url) {
                        document.execCommand(command, false, url);
                    }
                } else if (value) {
                    document.execCommand(command, false, value);
                } else {
                    document.execCommand(command, false, null);
                }
            }
        });
        
        // Make textarea a contenteditable div for rich text editing
        const editorContainer = document.createElement('div');
        editorContainer.className = 'editor-container';
        editorContainer.contentEditable = true;
        editorContainer.innerHTML = contentEditor.value || '<p>Start writing your blog post here...</p>';
        
        // Replace textarea with div
        contentEditor.style.display = 'none';
        contentEditor.parentNode.insertBefore(editorContainer, contentEditor.nextSibling);
        
        // Sync content back to textarea on form submit
        contentEditor.form.addEventListener('submit', function() {
            contentEditor.value = editorContainer.innerHTML;
        });
    }
});

// Image preview for uploads
document.querySelectorAll('input[type="file"]').forEach(input => {
    if (input.accept && input.accept.includes('image')) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    // Create preview image
                    let preview = input.parentNode.querySelector('.image-preview');
                    if (!preview) {
                        preview = document.createElement('div');
                        preview.className = 'image-preview';
                        input.parentNode.appendChild(preview);
                    }
                    
                    preview.innerHTML = `
                        <img src="${e.target.result}" alt="Preview">
                        <button type="button" class="remove-image">×</button>
                    `;
                    
                    // Add remove functionality
                    preview.querySelector('.remove-image').addEventListener('click', function() {
                        input.value = '';
                        preview.remove();
                    });
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

// Auto-generate excerpt from content
document.addEventListener('input', function(e) {
    if (e.target.id === 'content' || e.target.classList.contains('editor-container')) {
        const content = e.target.value || e.target.textContent;
        const excerptField = document.getElementById('excerpt');
        
        if (excerptField && !excerptField.value) {
            // Generate excerpt (first 150 characters)
            const plainText = content.replace(/<[^>]*>/g, '');
            if (plainText.length > 150) {
                excerptField.value = plainText.substring(0, 150) + '...';
            } else {
                excerptField.value = plainText;
            }
        }
    }
});

// Confirm delete actions
document.querySelectorAll('form[action*="delete"]').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
            e.preventDefault();
        }
    });
});

// Search functionality with debounce
let searchTimeout;
const searchInput = document.querySelector('.search-input');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            // Submit form on search
            this.form.submit();
        }, 500);
    });
}

// Update reading time
function updateReadingTime() {
    const article = document.querySelector('.post-content');
    if (article) {
        const text = article.textContent;
        const wordCount = text.split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / 200); // 200 words per minute
        
        const readingTimeElement = document.createElement('span');
        readingTimeElement.className = 'reading-time';
        readingTimeElement.innerHTML = `<i class="far fa-clock"></i> ${readingTime} min read`;
        
        const metaInfo = document.querySelector('.post-meta-info');
        if (metaInfo) {
            metaInfo.appendChild(readingTimeElement);
        }
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', updateReadingTime);