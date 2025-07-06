import React, { useState } from 'react';

const FileUploader = () => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
    setStatus('');
  };

  const handleUpload = async (fileToUpload: File) => {
    const formData = new FormData();
    formData.append('file', fileToUpload);

    try {
      const res = await fetch('http://localhost:3003/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) throw new Error('Upload failed.');

      const data = await res.json();
      setStatus(`✅ Uploaded: ${data.message}`);
    } catch (error) {
      setStatus(`❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="py-2 max-w-md">
      <label className="mb-4 bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-400 cursor-pointer inline-block">
        Choose Resume File
        <input
          type="file"
          onChange={async (e) => {
            handleFileChange(e);
            if (e.target.files && e.target.files[0]) {
              await handleUpload(e.target.files[0]);
            }
          }}
          className="hidden"
        />
      </label>

      {status && <p className="mt-4 text-sm">{status}</p>}
    </div>
  );
};

export default FileUploader;