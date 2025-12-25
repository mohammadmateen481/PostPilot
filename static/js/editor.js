// Rich Text Editor Enhancements

class RichTextEditor {
    constructor(textareaId) {
        this.textarea = document.getElementById(textareaId);
        this.editor = null;
        this.toolbar = null;
        this.init();
    }

    init() {
        this.createEditor();
        this.createToolbar();
        this.bindEvents();
        this.setupAutoSave();
    }

    createEditor() {
        // Create editor container
        this.editor = document.createElement('div');
        this.editor.className = 'rich-editor';
        this.editor.contentEditable = true;
        this.editor.innerHTML = this.textarea.value || '<p>Start writing...</p>';

        // Hide original textarea
        this.textarea.style.display = 'none';
        this.textarea.parentNode.insertBefore(this.editor, this.textarea.nextSibling);
    }

    createToolbar() {
        this.toolbar = document.createElement('div');
        this.toolbar.className = 'editor-toolbar';
        
        const buttons = [
            { command: 'bold', icon: 'fas fa-bold', title: 'Bold' },
            { command: 'italic', icon: 'fas fa-italic', title: 'Italic' },
            { command: 'underline', icon: 'fas fa-underline', title: 'Underline' },
            { separator: true },
            { command: 'formatBlock', value: 'h2', text: 'H2', title: 'Heading 2' },
            { command: 'formatBlock', value: 'h3', text: 'H3', title: 'Heading 3' },
            { command: 'formatBlock', value: 'p', text: 'P', title: 'Paragraph' },
            { separator: true },
            { command: 'insertUnorderedList', icon: 'fas fa-list-ul', title: 'Bullet List' },
            { command: 'insertOrderedList', icon: 'fas fa-list-ol', title: 'Numbered List' },
            { separator: true },
            { command: 'createLink', icon: 'fas fa-link', title: 'Insert Link' },
            { command: 'unlink', icon: 'fas fa-unlink', title: 'Remove Link' },
            { separator: true },
            { command: 'insertImage', icon: 'fas fa-image', title: 'Insert Image' },
            { separator: true },
            { command: 'undo', icon: 'fas fa-undo', title: 'Undo' },
            { command: 'redo', icon: 'fas fa-redo', title: 'Redo' }
        ];

        buttons.forEach(btn => {
            if (btn.separator) {
                const separator = document.createElement('span');
                separator.className = 'toolbar-separator';
                this.toolbar.appendChild(separator);
            } else {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'editor-btn';
                button.dataset.command = btn.command;
                if (btn.value) button.dataset.value = btn.value;
                button.title = btn.title;
                
                if (btn.icon) {
                    button.innerHTML = `<i class="${btn.icon}"></i>`;
                } else {
                    button.textContent = btn.text;
                }
                
                button.addEventListener('click', (e) => this.handleCommand(e));
                this.toolbar.appendChild(button);
            }
        });

        // Insert toolbar before editor
        this.editor.parentNode.insertBefore(this.toolbar, this.editor);
    }

    handleCommand(e) {
        e.preventDefault();
        const button = e.currentTarget;
        const command = button.dataset.command;
        const value = button.dataset.value;

        this.editor.focus();

        if (command === 'createLink') {
            const url = prompt('Enter URL:', 'https://');
            if (url) {
                document.execCommand(command, false, url);
            }
        } else if (command === 'insertImage') {
            this.insertImage();
        } else if (value) {
            document.execCommand(command, false, value);
        } else {
            document.execCommand(command, false, null);
        }

        this.updateTextarea();
        this.updateStats();
    }

    insertImage() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.style.display = 'none';

        input.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Create image upload form
                const formData = new FormData();
                formData.append('image', file);

                // Upload image
                fetch('/api/upload-image', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.url) {
                        document.execCommand('insertImage', false, data.url);
                        this.updateTextarea();
                    }
                })
                .catch(error => {
                    console.error('Error uploading image:', error);
                    alert('Failed to upload image');
                });
            }
        });

        document.body.appendChild(input);
        input.click();
        document.body.removeChild(input);
    }

    bindEvents() {
        // Sync editor content to textarea
        this.editor.addEventListener('input', () => {
            this.updateTextarea();
            this.updateStats();
        });

        // Handle paste events
        this.editor.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = e.clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });

        // Handle form submit
        const form = this.textarea.closest('form');
        if (form) {
            form.addEventListener('submit', () => {
                this.updateTextarea();
            });
        }
    }

    updateTextarea() {
        this.textarea.value = this.editor.innerHTML;
    }

    updateStats() {
        const text = this.editor.textContent;
        const words = text.trim().split(/\s+/).filter(w => w.length > 0);
        const characters = text.length;

        // Update stats display if exists
        const statsContainer = document.querySelector('.editor-stats');
        if (statsContainer) {
            const wordCount = statsContainer.querySelector('.word-count');
            const charCount = statsContainer.querySelector('.char-count');
            
            if (wordCount) wordCount.textContent = `${words.length} words`;
            if (charCount) charCount.textContent = `${characters} characters`;
        }
    }

    setupAutoSave() {
        let saveTimeout;
        const AUTO_SAVE_KEY = 'editor_autosave';

        const saveDraft = () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                const draft = {
                    content: this.editor.innerHTML,
                    timestamp: new Date().toISOString()
                };
                localStorage.setItem(AUTO_SAVE_KEY, JSON.stringify(draft));
            }, 2000);
        };

        this.editor.addEventListener('input', saveDraft);

        // Load draft on page load
        window.addEventListener('load', () => {
            const saved = localStorage.getItem(AUTO_SAVE_KEY);
            if (saved) {
                const draft = JSON.parse(saved);
                if (draft.content && !this.textarea.value) {
                    if (confirm('Found an unsaved draft. Load it?')) {
                        this.editor.innerHTML = draft.content;
                        this.updateTextarea();
                        this.updateStats();
                    }
                }
            }
        });

        // Clear draft on successful save
        const form = this.textarea.closest('form');
        if (form) {
            form.addEventListener('submit', () => {
                localStorage.removeItem(AUTO_SAVE_KEY);
            });
        }
    }

    // Public methods
    getContent() {
        return this.editor.innerHTML;
    }

    setContent(html) {
        this.editor.innerHTML = html;
        this.updateTextarea();
        this.updateStats();
    }

    focus() {
        this.editor.focus();
    }

    clear() {
        this.editor.innerHTML = '<p>Start writing...</p>';
        this.updateTextarea();
        this.updateStats();
    }
}

// Initialize editor when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const contentEditor = document.getElementById('content');
    if (contentEditor) {
        window.editor = new RichTextEditor('content');
    }
});

// Additional editor utilities
function formatText(command, value = null) {
    if (window.editor) {
        window.editor.focus();
        if (value) {
            document.execCommand(command, false, value);
        } else {
            document.execCommand(command, false, null);
        }
        window.editor.updateTextarea();
    }
}

function insertHTML(html) {
    if (window.editor) {
        window.editor.focus();
        document.execCommand('insertHTML', false, html);
        window.editor.updateTextarea();
    }
}

function insertTable(rows = 3, cols = 3) {
    let tableHTML = '<table border="1" style="border-collapse: collapse; width: 100%;">';
    for (let i = 0; i < rows; i++) {
        tableHTML += '<tr>';
        for (let j = 0; j < cols; j++) {
            tableHTML += `<td style="padding: 8px;">&nbsp;</td>`;
        }
        tableHTML += '</tr>';
    }
    tableHTML += '</table>';
    
    insertHTML(tableHTML);
}

function insertCode(code, language = '') {
    const codeHTML = `<pre><code class="language-${language}">${escapeHtml(code)}</code></pre>`;
    insertHTML(codeHTML);
}

function insertQuote(text, author = '') {
    let quoteHTML = '<blockquote style="border-left: 4px solid #ccc; margin: 20px 0; padding-left: 20px;">';
    quoteHTML += `<p>${escapeHtml(text)}</p>`;
    if (author) {
        quoteHTML += `<cite>— ${escapeHtml(author)}</cite>`;
    }
    quoteHTML += '</blockquote>';
    
    insertHTML(quoteHTML);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && window.editor && document.activeElement === window.editor.editor) {
        switch(e.key.toLowerCase()) {
            case 'b':
                e.preventDefault();
                formatText('bold');
                break;
            case 'i':
                e.preventDefault();
                formatText('italic');
                break;
            case 'u':
                e.preventDefault();
                formatText('underline');
                break;
            case 'k':
                e.preventDefault();
                formatText('createLink');
                break;
            case 'z':
                if (e.shiftKey) {
                    e.preventDefault();
                    formatText('redo');
                } else {
                    e.preventDefault();
                    formatText('undo');
                }
                break;
            case 's':
                e.preventDefault();
                // Auto-save or submit form
                const form = window.editor.textarea.closest('form');
                if (form) {
                    const saveBtn = form.querySelector('button[type="submit"]');
                    if (saveBtn) saveBtn.click();
                }
                break;
        }
    }
});

// Export editor functions
window.RichTextEditor = RichTextEditor;
window.editorUtils = {
    formatText,
    insertHTML,
    insertTable,
    insertCode,
    insertQuote
};