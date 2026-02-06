
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileName = document.getElementById('fileName');
        const uploadForm = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const submitBtn = document.getElementById('submitBtn');

       
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

       
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragover');
            }, false);
        });

     
        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                updateFileName(files[0].name);
            }
        }, false);

        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                updateFileName(e.target.files[0].name);
            }
        });

        function updateFileName(name) {
            fileName.textContent = `📄 ${name}`;
            fileName.style.color = '#28a745';
            fileName.style.fontWeight = '600';
        }

      
        uploadForm.addEventListener('submit', (e) => {
            if (fileInput.files.length === 0) {
                e.preventDefault();
                alert('⚠️ Por favor selecciona una imagen primero');
                return;
            }

            loading.classList.add('active');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analizando...';
        });

        
        window.addEventListener('load', () => {
            const confidenceFill = document.querySelector('.confidence-fill');
            if (confidenceFill) {
                const targetWidth = confidenceFill.style.width;
                confidenceFill.style.width = '0%';
                setTimeout(() => {
                    confidenceFill.style.width = targetWidth;
                }, 100);
            }
        });