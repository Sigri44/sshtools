#!/usr/bin/env python3

import sys
import os
import json
import zipfile
from io import BytesIO

# Python 2 and 3 compatibility
if sys.version_info[0] == 2:
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import TCPServer
    from urlparse import parse_qs
    from cgi import FieldStorage
    input_func = raw_input
else:
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer
    from urllib.parse import parse_qs, unquote
    from cgi import FieldStorage
    input_func = input

class FileUploadHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/upload':
            try:
                form = FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={
                        'REQUEST_METHOD': 'POST',
                        'CONTENT_TYPE': self.headers['Content-Type']
                    }
                )

                uploaded_files = []
                if 'file[]' in form:
                    # Handle multiple files (including directory structure)
                    items = form['file[]']
                    if not isinstance(items, list):
                        items = [items]

                    for item in items:
                        if hasattr(item, 'filename') and item.filename:
                            try:
                                # Create directory structure if needed
                                filepath = os.path.join(os.getcwd(), item.filename)
                                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                                
                                with open(filepath, 'wb') as f:
                                    f.write(item.file.read())
                                uploaded_files.append(item.filename)
                            except OSError as e:
                                self.send_error_page(
                                    "Upload Error",
                                    f"Error uploading {item.filename}",
                                    str(e),
                                    "The file might already exist or you don't have permission to write in this location."
                                )
                                return

                response = '''
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Upload Success</title>
                    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
                    <style>
                        :root {
                            --bg-color: #1a1b1e;
                            --card-bg: #25262b;
                            --text-color: #c1c2c5;
                            --accent-color: #22c55e;
                            --border-color: #2c2d31;
                        }
                        
                        body {
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
                            line-height: 1.5;
                            color: var(--text-color);
                            background: var(--bg-color);
                            margin: 0;
                            padding: 24px;
                            font-size: 14px;
                        }
                        
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                            background: var(--card-bg);
                            border-radius: 12px;
                            padding: 24px;
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                        }
                        
                        .success-icon {
                            font-size: 48px;
                            color: var(--accent-color);
                            margin-bottom: 16px;
                            text-align: center;
                        }
                        
                        h2 {
                            color: var(--text-color);
                            margin: 0 0 16px 0;
                            text-align: center;
                        }
                        
                        ul {
                            list-style: none;
                            padding: 0;
                            margin: 16px 0;
                        }
                        
                        li {
                            padding: 8px 0;
                            border-bottom: 1px solid var(--border-color);
                        }
                        
                        li:last-child {
                            border-bottom: none;
                        }
                        
                        .btn {
                            display: inline-flex;
                            align-items: center;
                            gap: 8px;
                            padding: 10px 20px;
                            font-size: 14px;
                            font-weight: 500;
                            color: #fff;
                            background: var(--accent-color);
                            border: none;
                            border-radius: 8px;
                            cursor: pointer;
                            text-decoration: none;
                            transition: all 0.3s ease;
                        }
                        
                        .btn:hover {
                            opacity: 0.9;
                            transform: translateY(-1px);
                        }
                        
                        .center {
                            text-align: center;
                            margin-top: 24px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success-icon">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <h2>Upload Successful!</h2>
                '''
                if len(uploaded_files) > 1:
                    response += f'<p>{len(uploaded_files)} files were uploaded successfully:</p><ul>'
                    for f in uploaded_files:
                        response += f'<li><i class="fas fa-file"></i> {f}</li>'
                    response += '</ul>'
                elif len(uploaded_files) == 1:
                    response += f'<p><i class="fas fa-file"></i> {uploaded_files[0]} was uploaded successfully.</p>'
                else:
                    response += '<p>No files were uploaded.</p>'
                
                response += '''
                        <div class="center">
                            <a href="/" class="btn">
                                <i class="fas fa-arrow-left"></i> Back to Files
                            </a>
                        </div>
                    </div>
                </body>
                </html>'''
                
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(response.encode())
                return
            except Exception as e:
                self.send_error_page(
                    "Upload Error",
                    "Failed to process upload",
                    str(e),
                    "There was an error processing your upload request. Please try again."
                )
                return
        elif self.path == '/download-selected':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                files = json.loads(post_data)

                # Create a ZIP file in memory
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for file_path in files:
                        if os.path.exists(file_path):
                            if os.path.isdir(file_path):
                                # Walk through directory
                                for root, dirs, files in os.walk(file_path):
                                    for file in files:
                                        full_path = os.path.join(root, file)
                                        arcname = os.path.relpath(full_path, os.path.dirname(file_path))
                                        zip_file.write(full_path, arcname)
                            else:
                                # Single file
                                zip_file.write(file_path, os.path.basename(file_path))

                # Send the ZIP file
                self.send_response(200)
                self.send_header('Content-type', 'application/zip')
                self.send_header('Content-Disposition', 'attachment; filename=\"selected_files.zip\"')
                self.end_headers()
                self.wfile.write(zip_buffer.getvalue())
                return
            except Exception as e:
                self.send_error_page(
                    "Download Error",
                    "Failed to create download",
                    str(e),
                    "There was an error creating the zip file for download. Please try again."
                )
                return

    def send_error_page(self, title, heading, error_message, suggestion):
        """Send a custom error page"""
        error_html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
            <style>
                :root {{
                    --bg-color: #1a1b1e;
                    --card-bg: #25262b;
                    --text-color: #c1c2c5;
                    --error-color: #ef4444;
                    --border-color: #2c2d31;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
                    line-height: 1.5;
                    color: var(--text-color);
                    background: var(--bg-color);
                    margin: 0;
                    padding: 24px;
                    font-size: 14px;
                }}
                
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: var(--card-bg);
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                }}
                
                .error-icon {{
                    font-size: 48px;
                    color: var(--error-color);
                    margin-bottom: 16px;
                    text-align: center;
                }}
                
                h2 {{
                    color: var(--text-color);
                    margin: 0 0 16px 0;
                    text-align: center;
                }}
                
                .error-details {{
                    background: rgba(239, 68, 68, 0.1);
                    border: 1px solid var(--error-color);
                    border-radius: 8px;
                    padding: 16px;
                    margin: 16px 0;
                    color: var(--text-color);
                }}
                
                .suggestion {{
                    color: #6b7280;
                    margin: 16px 0;
                    padding: 16px;
                    border-left: 4px solid var(--border-color);
                }}
                
                .btn {{
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: 500;
                    color: #fff;
                    background: var(--error-color);
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    text-decoration: none;
                    transition: all 0.3s ease;
                }}
                
                .btn:hover {{
                    opacity: 0.9;
                    transform: translateY(-1px);
                }}
                
                .center {{
                    text-align: center;
                    margin-top: 24px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">
                    <i class="fas fa-exclamation-circle"></i>
                </div>
                <h2>{heading}</h2>
                <div class="error-details">
                    <strong>Error:</strong> {error_message}
                </div>
                <div class="suggestion">
                    <i class="fas fa-lightbulb"></i> {suggestion}
                </div>
                <div class="center">
                    <a href="/" class="btn">
                        <i class="fas fa-arrow-left"></i> Back to Files
                    </a>
                </div>
            </div>
        </body>
        </html>
        '''
        
        self.send_response(500)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(error_html.encode())

    def list_directory(self, path):
        try:
            list = os.listdir(path)
        except OSError:
            self.send_error(404, 'No permission to list directory')
            return None
        
        list.sort(key=lambda a: a.lower())
        
        r = []
        r.append('<!DOCTYPE html>')
        r.append('<html>')
        r.append('<head>')
        r.append('    <meta charset="utf-8">')
        r.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
        r.append('    <title>WebShare</title>')
        r.append('    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">')
        r.append(r'''    <style>
        :root {
            --bg-color: #1a1b1e;
            --card-bg: #25262b;
            --text-color: #c1c2c5;
            --accent-color: #3b82f6;
            --border-color: #2c2d31;
            --hover-bg: #2c2d31;
            --danger-color: #ef4444;
            --success-color: #22c55e;
            --folder-color: #3b82f6;
            --file-color: #94a3b8;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
            line-height: 1.5;
            color: var(--text-color);
            background: var(--bg-color);
            font-size: 14px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px;
        }
        
        .header {
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 16px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-color);
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
        }
        
        .header h1 i {
            color: var(--accent-color);
        }

        .server-info {
            display: flex;
            align-items: center;
            gap: 24px;
            color: #6b7280;
            font-size: 14px;
        }

        .server-info span {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .server-info i {
            font-size: 14px;
            opacity: 0.8;
        }

        .server-info .hostname {
            color: var(--accent-color);
            font-weight: 500;
        }

        .server-info .path {
            color: var(--success-color);
            font-weight: 500;
            word-break: break-all;
        }
        
        .upload-zone {
            background: var(--card-bg);
            border: 2px dashed var(--border-color);
            border-radius: 12px;
            padding: 32px;
            text-align: center;
            margin-bottom: 24px;
            transition: all 0.3s ease;
            position: relative;
        }
        
        .upload-zone:hover, .upload-zone.dragover {
            border-color: var(--accent-color);
            background: rgba(59, 130, 246, 0.05);
        }
        
        .upload-zone i {
            font-size: 48px;
            color: var(--text-color);
            margin-bottom: 16px;
            opacity: 0.8;
        }
        
        .upload-zone h3 {
            font-size: 18px;
            margin-bottom: 8px;
            color: var(--text-color);
        }
        
        .upload-zone p {
            color: #6b7280;
            margin-bottom: 24px;
        }

        .upload-zone form {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 16px;
        }

        .upload-zone input[type="file"] {
            display: none;
        }

        .upload-btn, .file-input-label {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            padding: 0 24px;
            font-size: 14px;
            font-weight: 500;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            height: 42px;
            min-width: 140px;
        }

        .upload-btn {
            color: #fff;
            background: linear-gradient(45deg, var(--accent-color), #2563eb);
            border: none;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.2);
        }
        
        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px -1px rgba(59, 130, 246, 0.3);
            background: linear-gradient(45deg, #2563eb, #1d4ed8);
        }
        
        .upload-btn:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px -1px rgba(59, 130, 246, 0.2);
        }
        
        .upload-btn i {
            font-size: 16px;
            color: #fff;
            margin-bottom: 4px;
        }

        .file-input-label {
            color: var(--text-color);
            background: var(--hover-bg);
            border: 1px solid var(--border-color);
        }

        .file-input-label:hover {
            background: var(--card-bg);
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }

        .file-input-label i {
            font-size: 16px;
            color: var(--accent-color);
            margin-bottom: 4px;
        }
        
        .search-container {
            position: relative;
            margin-bottom: 24px;
        }
        
        .search-box {
            width: 100%;
            padding: 12px 20px;
            font-size: 14px;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-color);
            transition: all 0.3s ease;
        }
        
        .search-box:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
        }
        
        .search-icon {
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #6b7280;
        }
        
        .files-table {
            width: 100%;
            background: var(--card-bg);
            border-radius: 12px;
            border-collapse: separate;
            border-spacing: 0;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .files-table th {
            background: var(--hover-bg);
            padding: 16px;
            font-weight: 600;
            color: var(--text-color);
            text-align: left;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }
        
        .files-table th i {
            margin-left: 8px;
            opacity: 0.5;
        }
        
        .files-table th:hover {
            background: var(--card-bg);
        }
        
        .files-table th.sorted-asc i.fa-sort-up,
        .files-table th.sorted-desc i.fa-sort-down {
            opacity: 1;
            color: var(--accent-color);
        }
        
        .files-table td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .files-table tr:hover td {
            background: var(--hover-bg);
        }
        
        .files-table tr:last-child td {
            border-bottom: none;
        }
        
        .checkbox-column {
            width: 40px;
            text-align: center;
        }
        
        .name-column {
            width: 60%;
        }
        
        .file-icon {
            margin-right: 12px;
            font-size: 16px;
        }
        
        .folder .file-icon {
            color: var(--folder-color);
        }
        
        .file .file-icon {
            color: var(--file-color);
        }
        
        a {
            color: var(--text-color);
            text-decoration: none;
            transition: color 0.3s ease;
        }
        
        a:hover {
            color: var(--accent-color);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
            color: #fff;
            background: var(--accent-color);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }
        
        .btn i {
            font-size: 16px;
        }
        
        .actions {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 24px;
        }
        
        #selected-count {
            padding: 8px 16px;
            background: var(--card-bg);
            border-radius: 8px;
            color: #6b7280;
        }
        
        input[type="checkbox"] {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            border: 1px solid var(--border-color);
            background: var(--card-bg);
            cursor: pointer;
        }
        
        .hidden {
            display: none;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .header {
                padding: 16px;
            }
            
            .upload-zone {
                padding: 24px;
            }
            
            .date {
                display: none;
            }
            
            .files-table td, .files-table th {
                padding: 12px;
            }
            
            .name-column {
                width: auto;
            }
        }
    </style>''')
        r.append(r'''    <script>
        function handleDragOver(evt) {
            evt.preventDefault();
            evt.target.classList.add("dragover");
        }
        
        function handleDragLeave(evt) {
            evt.target.classList.remove("dragover");
        }
        
        function handleDrop(evt) {
            evt.preventDefault();
            evt.target.classList.remove("dragover");
            var files = evt.dataTransfer.files;
            var formData = new FormData();
            
            for (var i = 0; i < files.length; i++) {
                formData.append('file[]', files[i], files[i].webkitRelativePath || files[i].name);
            }
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            }).then(response => response.text())
              .then(html => {
                  document.body.innerHTML = html;
              });
        }

        function searchFiles() {
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();
            const rows = document.querySelectorAll('.files-table tr:not(:first-child)');
            let visibleCount = 0;

            rows.forEach(row => {
                const fileName = row.querySelector('.name-column').textContent.toLowerCase();
                if (fileName.includes(searchTerm)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
        }

        function toggleAll(source) {
            const checkboxes = document.getElementsByName('file-select');
            for (let checkbox of checkboxes) {
                checkbox.checked = source.checked;
            }
            updateSelectedCount();
        }

        function updateSelectedCount() {
            const selectedFiles = document.querySelectorAll('input[name="file-select"]:checked').length;
            const selectedSize = calculateSelectedSize();
            document.getElementById('selected-count').textContent = `${selectedFiles} item(s) selected (${formatSize(selectedSize)})`;
        }

        function calculateSelectedSize() {
            let totalSize = 0;
            const checkboxes = document.querySelectorAll('input[name="file-select"]:checked');
            checkboxes.forEach(checkbox => {
                const row = checkbox.closest('tr');
                const sizeCell = row.querySelector('.size');
                const sizeText = sizeCell.getAttribute('data-size') || '0';
                totalSize += parseInt(sizeText, 10);
            });
            return totalSize;
        }

        function formatSize(bytes) {
            const units = ['B', 'KB', 'MB', 'GB', 'TB'];
            let size = bytes;
            let unitIndex = 0;
            while (size >= 1024 && unitIndex < units.length - 1) {
                size /= 1024;
                unitIndex++;
            }
            return unitIndex === 0 ? size + ' ' + units[unitIndex] : size.toFixed(1) + ' ' + units[unitIndex];
        }

        function downloadSelected() {
            const checkboxes = document.getElementsByName('file-select');
            const selectedFiles = [];
            
            for (let checkbox of checkboxes) {
                if (checkbox.checked) {
                    selectedFiles.push(checkbox.value);
                }
            }

            if (selectedFiles.length === 0) {
                alert('Please select at least one item to download');
                return;
            }

            fetch('/download-selected', {
                method: 'POST',
                body: JSON.stringify(selectedFiles)
            }).then(response => response.blob())
              .then(blob => {
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'selected_files.zip';
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
              });
        }

        function sortTable(columnIndex) {
            const table = document.querySelector('.files-table');
            const header = table.querySelector(`th:nth-child(${columnIndex + 1})`);
            const isAsc = !header.classList.contains('sorted-asc');
            
            // Remove sorting classes from all headers
            table.querySelectorAll('th').forEach(th => {
                th.classList.remove('sorted-asc', 'sorted-desc');
                const icon = th.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-sort';
                }
            });
            
            // Add sorting class to clicked header
            header.classList.add(isAsc ? 'sorted-asc' : 'sorted-desc');
            const icon = header.querySelector('i');
            if (icon) {
                icon.className = `fas fa-sort-${isAsc ? 'up' : 'down'}`;
            }
            
            const tbody = table.querySelector('tbody') || table;
            const rows = Array.from(tbody.querySelectorAll('tr:not(:first-child)'));
            
            const sortedRows = rows.sort((a, b) => {
                let aValue = a.querySelector(`td:nth-child(${columnIndex + 1})`).textContent.trim();
                let bValue = b.querySelector(`td:nth-child(${columnIndex + 1})`).textContent.trim();
                
                // Handle name column - remove icon from comparison
                if (columnIndex === 1) {
                    aValue = aValue.replace(/^[\u{1F300}-\u{1F9FF}]|^[\u2600-\u26FF]|\s+$/gu, '').trim();
                    bValue = bValue.replace(/^[\u{1F300}-\u{1F9FF}]|^[\u2600-\u26FF]|\s+$/gu, '').trim();
                }
                
                // Handle size sorting
                if (columnIndex === 3) {
                    aValue = parseInt(a.querySelector('.size').getAttribute('data-size'));
                    bValue = parseInt(b.querySelector('.size').getAttribute('data-size'));
                    return isAsc ? aValue - bValue : bValue - aValue;
                }
                
                // Handle date sorting
                if (columnIndex === 4) {
                    aValue = new Date(aValue).getTime();
                    bValue = new Date(bValue).getTime();
                    return isAsc ? aValue - bValue : bValue - aValue;
                }
                
                // Default string comparison
                return isAsc ? 
                    aValue.localeCompare(bValue, undefined, {numeric: true, sensitivity: 'base'}) :
                    bValue.localeCompare(aValue, undefined, {numeric: true, sensitivity: 'base'});
            });
            
            // Remove existing rows
            rows.forEach(row => row.remove());
            
            // Add sorted rows
            sortedRows.forEach(row => tbody.appendChild(row));
        }
    </script>''')
        r.append('</head>')
        r.append('<body>')
        r.append('    <div class="container">')
        r.append('        <div class="header">')
        r.append('            <h1><i class="fas fa-share-nodes"></i> WebShare</h1>')
        r.append(f'''            <div class="server-info">
                <span><i class="fas fa-server"></i>Server: <span class="hostname">{os.uname().nodename}</span></span>
                <span><i class="fas fa-folder"></i>Path: <span class="path">{os.getcwd()}</span></span>
            </div>''')
        r.append('        </div>')
        r.append(r'''        <div class="upload-zone" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)" ondrop="handleDrop(event)">
            <i class="fas fa-cloud-upload-alt"></i>
            <h3>Upload Files or Directory</h3>
            <p>Drag & drop files here or select files to upload</p>
            <form id="uploadForm" enctype="multipart/form-data" method="post" action="/upload">
                <label for="fileInput" class="file-input-label">
                    <i class="fas fa-folder-open"></i>
                    Choose Files
                </label>
                <input type="file" name="file[]" id="fileInput" webkitdirectory directory multiple>
                <button type="submit" class="upload-btn">
                    <i class="fas fa-upload"></i>
                    Upload Files
                </button>
            </form>
        </div>''')
        r.append(r'''        <div class="search-container">
            <input type="text" id="searchBox" class="search-box" placeholder="Search files..." oninput="searchFiles()">
            <i class="fas fa-search search-icon"></i>
        </div>''')
        r.append(r'''        <div class="actions">
            <button onclick="downloadSelected()" class="btn">
                <i class="fas fa-download"></i> Download Selected
            </button>
            <span id="selected-count">0 items selected</span>
        </div>''')
        r.append('        <table class="files-table">')
        r.append(r'''            <tr>
                <th class="checkbox-column"><input type="checkbox" onclick="toggleAll(this)"></th>
                <th class="name-column" onclick="sortTable(1)">Name <i class="fas fa-sort"></i></th>
                <th onclick="sortTable(2)">Type <i class="fas fa-sort"></i></th>
                <th onclick="sortTable(3)">Size <i class="fas fa-sort"></i></th>
                <th class="date" onclick="sortTable(4)">Last Modified <i class="fas fa-sort"></i></th>
            </tr>''')

        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            file_type = ""
            
            if os.path.isdir(fullname):
                displayname = name
                linkname = name + '/'
                icon_class = 'folder'
                icon = '<i class="fas fa-folder file-icon"></i>'
                file_type = "Directory"
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(fullname):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        try:
                            total_size += os.path.getsize(fp)
                        except OSError:
                            pass
                size = total_size
                size_str = self._format_size(size)
            else:
                icon_class = 'file'
                ext = os.path.splitext(name)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    icon = '<i class="fas fa-image file-icon"></i>'
                    file_type = "Image"
                elif ext in ['.mp3', '.wav', '.ogg']:
                    icon = '<i class="fas fa-music file-icon"></i>'
                    file_type = "Audio"
                elif ext in ['.mp4', '.avi', '.mkv', '.mov']:
                    icon = '<i class="fas fa-video file-icon"></i>'
                    file_type = "Video"
                elif ext in ['.pdf']:
                    icon = '<i class="fas fa-file-pdf file-icon"></i>'
                    file_type = "PDF"
                elif ext in ['.doc', '.docx']:
                    icon = '<i class="fas fa-file-word file-icon"></i>'
                    file_type = "Word"
                elif ext in ['.xls', '.xlsx']:
                    icon = '<i class="fas fa-file-excel file-icon"></i>'
                    file_type = "Excel"
                elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
                    icon = '<i class="fas fa-file-archive file-icon"></i>'
                    file_type = "Archive"
                elif ext in ['.txt', '.md']:
                    icon = '<i class="fas fa-file-alt file-icon"></i>'
                    file_type = "Text"
                elif ext in ['.py', '.js', '.html', '.css', '.php', '.java', '.cpp']:
                    icon = '<i class="fas fa-file-code file-icon"></i>'
                    file_type = "Code"
                else:
                    icon = '<i class="fas fa-file file-icon"></i>'
                    file_type = ext[1:].upper() if ext else "File"
                try:
                    size = os.path.getsize(fullname)
                    size_str = self._format_size(size)
                except OSError:
                    size = 0
                    size_str = '???'
                
            if os.path.islink(fullname):
                displayname = name
                icon = '<i class="fas fa-link file-icon"></i>'
                file_type = "Link"
                
            try:
                mtime = os.path.getmtime(fullname)
                mtime_str = self._format_date(mtime)
            except OSError:
                mtime_str = '???'
                
            checkbox = '<input type="checkbox" name="file-select" value="{}" onclick="updateSelectedCount()">'.format(fullname)
            
            r.append('            <tr class="{}-row">'.format(icon_class))
            r.append('                <td class="checkbox-column">{}</td>'.format(checkbox))
            r.append('                <td class="name-column"><a href="{}" class="{}">{}{}</a></td>'.format(linkname, icon_class, icon, displayname))
            r.append('                <td class="type">{}</td>'.format(file_type))
            r.append('                <td class="size" data-size="{}">{}</td>'.format(size, size_str))
            r.append('                <td class="date">{}</td>'.format(mtime_str))
            r.append('            </tr>')
            
        r.append('        </table>')
        r.append('    </div>')
        r.append('''    <div style="text-align: center; padding: 20px; margin-top: 40px; color: var(--text-color); border-top: 1px solid var(--border-color);">
        Made by <a href="https://github.com/PAPAMICA" style="color: var(--accent-color); text-decoration: none;">Mickael Asseline</a> with ♥️ - <a href="https://github.com/PAPAMICA/sshtools" style="color: var(--accent-color); text-decoration: none;">SSHTools</a>
    </div>''')
        r.append('</body>')
        r.append('</html>')
        
        encoded = '\n'.join(r).encode('utf-8', 'replace')
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)
        return None
        
    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                if unit == 'B':
                    return '%d %s' % (size, unit)
                return '%.1f %s' % (size, unit)
            size /= 1024
        return '%.1f TB' % size
        
    def _format_date(self, timestamp):
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def main():
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid port number '{sys.argv[1]}'")
            sys.exit(1)
    else:
        port = 8000

    Handler = FileUploadHandler
    TCPServer.allow_reuse_address = True
    
    try:
        httpd = TCPServer(('', port), Handler)
        
        # Get IP addresses using shell command
        import subprocess
        cmd = "ifconfig 2>/dev/null | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}'"
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, _ = process.communicate()
        addresses = output.decode().strip().split('\n')
        addresses = [addr for addr in addresses if addr]  # Filter out empty strings
        
        print(f"\n🌐 Web File Server started")
        print(f"📂 Sharing directory: {os.getcwd()}")
        print(f"🔌 Available on:")
        print(f"   • Local:   http://localhost:{port}")
        for ip in addresses:
            print(f"   • Network: http://{ip}:{port}")
        print("\n💡 Press Ctrl+C to stop the server\n")
        
        httpd.serve_forever()
    except OSError as e:
        if e.errno == 98:
            print(f"\n❌ Error: Port {port} is already in use")
        else:
            print(f"\n❌ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print('\n👋 Shutting down server...')
        httpd.shutdown()
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    main()