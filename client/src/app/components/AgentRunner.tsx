import React, { useState, useEffect } from 'react';
import 'jspdf'
import 'html2pdf.js'

interface Job {
  title: string;
  job_url: string;
  score: number;
  location: string;
  is_remote: boolean;
  curated: boolean;
}

const AgentRunner: React.FC = () => {
  const [fields, setFields] = useState({
    field1: '',
    field2: '',
    field3: '',
    field4: '',
    field5: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadingJobs] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields({
      ...fields,
      [e.target.name]: e.target.value,
    });
  };

  const handleAutomat = async () => {
    try {
      setIsLoading(true);

      const params = new URLSearchParams({
        search_term: fields.field1 || "software engineer",
        location: fields.field2 || "Phoenix, AZ",
        results_wanted: fields.field3 || "10",
        hours_old: fields.field4 || "24",
        country_indeed: fields.field5 || "USA",
      }).toString();
      const res = await fetch(`http://localhost:3003/api/automate?${params}`);

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      // Wait for automate to finish, then refresh the curated jobs table
      const data = await res.json();
      setJobs(data);
    } catch (err) {
      console.error('Post error:', err);
      setError('Error: ' + (err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  // Download resume as markdown or pdf file for a given job_url
  const handleDownloadResume = async (job_url: string, jobTitle: string, asPdf: boolean = false) => {
    try {
      const paramsObj: Record<string, string> = { job_url };
      const params = new URLSearchParams(paramsObj).toString();
      const res = await fetch(`http://localhost:3003/api/download_curated_resume?${params}`);
      if (!res.ok) throw new Error(`Error: ${res.status}`);

      const safeTitle = jobTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();
      const markdown = await res.text();

      if (asPdf) {
        // Convert markdown to HTML
        let html = '';
        try {
          const { marked } = await import('marked');
          html = marked.parse(markdown);
        } catch (e) {
          // fallback: wrap in <pre>
          html = `<pre>${markdown.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre>`;
        }

        // Create a temporary element to hold the HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        document.body.appendChild(tempDiv);

        // Use html2pdf to generate PDF from HTML
        await html2pdf()
          .from(tempDiv)
          .set({
            filename: `${safeTitle}_resume.pdf`,
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'pt', format: 'a4', orientation: 'portrait' }
          })
          .save();

        document.body.removeChild(tempDiv);
      } else {
        // Download as markdown
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${safeTitle}_resume.md`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }, 0);
      }
    } catch (err) {
      setError('Download error: ' + (err as Error).message);
    }
  };

  return (
    <div className="flex h-screen">
      {/* Left Section: 1/3 width */}
      <div className="w-1/3 max-w-md p-4 bg-white">
        <div className="mb-4">
          <label className="block mb-1" htmlFor="field1">Job Title</label>
          <input
            id="field1"
            name="field1"
            type="text"
            value={fields.field1}
            onChange={handleChange}
            placeholder="e.g. Software Engineer"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="field2">Location</label>
          <input
            id="field2"
            name="field2"
            type="text"
            value={fields.field2}
            onChange={handleChange}
            placeholder="e.g. Phoenix, AZ"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="field3">Result Limit</label>
          <input
            id="field3"
            name="field3"
            type="text"
            value={fields.field3}
            onChange={handleChange}
            placeholder="e.g. 10"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="field4">Hours Old</label>
          <input
            id="field4"
            name="field4"
            type="text"
            value={fields.field4}
            onChange={handleChange}
            placeholder="e.g. 24"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="field5">Country</label>
          <input
            id="field5"
            name="field5"
            type="text"
            value={fields.field5}
            onChange={handleChange}
            placeholder="e.g. USA"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <button
          onClick={handleAutomat}
          disabled={isLoading}
          className={`px-4 py-2 rounded ${isLoading
            ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
            : 'bg-gray-600 hover:bg-gray-400 text-white'
            }`}
          style={{ marginRight: '4px' }}
        >
          {isLoading ? 'Processing...' : 'Submit to Resume Agent'}
        </button>
      </div>
      {/* Right Section: 2/3 width */}
      <div className="w-2/3 p-6 flex flex-col">
        <div className="overflow-auto" style={{ minHeight: '300px', maxHeight: '600px' }}>
          {loadingJobs ? (
            <div className="text-gray-500">Loading curated jobs...</div>
          ) : error ? (
            <div className="text-red-500">Error: {error}</div>
          ) : (
            <table className="min-w-full border border-gray-300 rounded">
              <thead>
                <tr className="bg-gray-100">
                  <th className="px-4 py-2 border-b">Title</th>
                  <th className="px-4 py-2 border-b">Job URL</th>
                  <th className="px-4 py-2 border-b">Score</th>
                  <th className="px-4 py-2 border-b">Location</th>
                  <th className="px-4 py-2 border-b">Is Remote</th>
                  <th className="px-4 py-2 border-b">Curated</th>
                  <th className="px-4 py-2 border-b">Download Resume</th>
                </tr>
              </thead>
              <tbody>
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-4 text-gray-500">
                      No curated jobs found.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job, idx) => (
                    <tr key={job.job_url || idx} className="hover:bg-gray-50">
                      <td className="px-4 py-2 border-b">{job.title}</td>
                      <td className="px-4 py-2 border-b">
                        <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                          Link
                        </a>
                      </td>
                      <td className="px-4 py-2 border-b">{job.score}</td>
                      <td className="px-4 py-2 border-b">{job.location}</td>
                      <td className="px-4 py-2 border-b">{job.is_remote}</td>
                      <td className="px-4 py-2 border-b">{job.curated ? "Yes" : "No"}</td>
                      <td className="px-4 py-2 border-b flex flex-col gap-2">
                        <button
                          className="bg-blue-500 hover:bg-blue-700 text-white px-3 py-1 rounded mb-1"
                          onClick={() => handleDownloadResume(job.job_url, job.title)}
                        >
                          Download Resume
                        </button>
                        <button
                          className="bg-green-500 hover:bg-green-700 text-white px-3 py-1 rounded"
                          onClick={() => handleDownloadResume(job.job_url, job.title, true)}
                        >
                          Download Resume Pdf
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
export default AgentRunner;