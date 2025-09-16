// WYSIWYG Editor Core Functionality
class WysiwygEditor {
  constructor() {
    this.editors = new Map();
  }

  initialize(editor, textarea) {
    if (!editor || !textarea) return null;

    // Set initial content
    if (textarea.value) {
      editor.innerHTML = textarea.value;
    }

    const editorInstance = {
      element: editor,
      textarea: textarea,
      updatePlaceholder: this.createUpdatePlaceholder(editor),
      syncContent: this.createSyncContent(editor, textarea)
    };

    // Event listeners
    this.attachEventListeners(editorInstance);

    // Initial setup
    editorInstance.updatePlaceholder();
    editorInstance.syncContent();

    this.editors.set(editor.id, editorInstance);

    return {
      getContent: () => editor.innerHTML,
      setContent: (content) => {
        editor.innerHTML = content;
        editorInstance.syncContent();
      }
    };
  }

  createUpdatePlaceholder(editor) {
    return function() {
      const isEmpty = editor.innerHTML.trim() === '' || 
                     editor.innerHTML === '<br>' || 
                     editor.innerHTML === '<p><br></p>';
      editor.classList.toggle('is-empty', isEmpty);
    };
  }

  createSyncContent(editor, textarea) {
    return function() {
      textarea.value = editor.innerHTML;
      // Update placeholder after sync
      const isEmpty = editor.innerHTML.trim() === '' || 
                     editor.innerHTML === '<br>' || 
                     editor.innerHTML === '<p><br></p>';
      editor.classList.toggle('is-empty', isEmpty);
    };
  }

  attachEventListeners(editorInstance) {
    const { element: editor, syncContent, updatePlaceholder } = editorInstance;

    editor.addEventListener('input', syncContent);
    
    editor.addEventListener('paste', () => {
      setTimeout(syncContent, 10); // Allow paste to complete
    });
    
    editor.addEventListener('focus', updatePlaceholder);
    
    editor.addEventListener('blur', () => {
      updatePlaceholder();
      // Clean up empty paragraphs
      if (editor.innerHTML === '<p><br></p>' || editor.innerHTML === '<br>') {
        editor.innerHTML = '';
      }
      syncContent();
    });
    
    editor.addEventListener('keyup', () => {
      setTimeout(syncContent, 100);
    });
  }

  syncAllContent() {
    // Sync question content
    const questionEditor = document.querySelector('#wysiwyg-question-text-admin');
    const questionTextarea = document.querySelector('#id_question_text');
    if (questionEditor && questionTextarea) {
      questionTextarea.value = questionEditor.innerHTML;
    }
    
    // Sync explanation content
    const explanationEditor = document.querySelector('#wysiwyg-explanation-text-admin');
    const explanationTextarea = document.querySelector('#id_explanation');
    if (explanationEditor && explanationTextarea) {
      explanationTextarea.value = explanationEditor.innerHTML;
    }
    
    // Sync all choice editors
    for (let i = 1; i <= 5; i++) {
      const choiceEditor = document.querySelector(`#wysiwyg-choice-text-${i}`);
      const choiceTextarea = document.querySelector(`#id_choices-${i-1}-choice_text`);
      
      if (choiceEditor && choiceTextarea) {
        let htmlContent = choiceEditor.innerHTML;
        
        // Get text content to check if it's truly empty
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        const textContent = tempDiv.textContent || tempDiv.innerText || '';
        
        // Clean up empty WYSIWYG content (just empty tags)
        if (!textContent.trim()) {
          htmlContent = '';
        }
        
        choiceTextarea.value = htmlContent;
      }
    }
  }
}

// Global instance
window.wysiwygEditor = new WysiwygEditor();