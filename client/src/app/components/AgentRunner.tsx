import React, { useState, useEffect } from 'react';
import FileUploader from './FileUploader';

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
    search_term: '',
    location: '',
    result_limit: '',
    hours_old: '',
    country: '',
    minimum_score: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loadingJobs] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Track which jobs should have download disabled (by job_url)
  const [disabledDownloads, setDisabledDownloads] = useState<Record<string, boolean>>({});

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
        search_term: fields.search_term || "software engineer",
        location: fields.location || "",
        results_wanted: fields.result_limit || "10",
        hours_old: fields.hours_old || "24",
        country_indeed: fields.country || "USA",
        min_job_score: fields.minimum_score || "60",
      }).toString();
      const res = await fetch(`http://localhost:3003/api/automate?${params}`);

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      // Wait for automate to finish, then refresh the curated jobs table
      const data = await res.json();
      setJobs(data);

      // After jobs are loaded, update disabledDownloads for jobs below minimum score
      const minScore = getMinimumScore(fields.minimum_score);
      const disabled: Record<string, boolean> = {};
      (data as Job[]).forEach((job: Job) => {
        if (job.score <= minScore) {
          disabled[job.job_url] = true;
        }
      });
      setDisabledDownloads(disabled);
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
      const paramsObj: Record<string, string | boolean> = { job_url };
      if (asPdf) {
        paramsObj['asPdf'] = 'true';
      }
      const params = new URLSearchParams(paramsObj as Record<string, string>).toString();
      const res = await fetch(`http://localhost:3003/api/download_curated_resume?${params}`);

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      const safeTitle = jobTitle.replace(/[^a-z0-9]/gi, '_').toLowerCase();

      if (asPdf) {
        // Download as PDF
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${safeTitle}_resume.pdf`;
        document.body.appendChild(a);
        a.click();
        setTimeout(() => {
          document.body.removeChild(a);
          window.URL.revokeObjectURL(url);
        }, 0);
      } else {
        // Download as markdown
        const markdown = (await res.text()).replace(/"/g, '');
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

  // Helper to get minimum score as number
  const getMinimumScore = (minScoreStr?: string) => {
    const minScore = minScoreStr !== undefined ? minScoreStr : fields.minimum_score || "60";
    const parsed = parseFloat(minScore);
    return isNaN(parsed) ? 60 : parsed;
  };

  return (
    <div className="flex h-screen">
      {/* Left Section: 1/3 width */}
      <div className="w-1/3 max-w-md p-4 bg-white">
        {/* FileUploader added above the input boxes */}
        <div className="mb-6">
          <FileUploader />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="search_term">Job Title</label>
          <input
            id="search_term"
            name="search_term"
            type="text"
            value={fields.search_term}
            onChange={handleChange}
            placeholder="e.g. Software Engineer"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="location">Location</label>
          <input
            id="location"
            name="location"
            type="text"
            value={fields.location}
            onChange={handleChange}
            placeholder="e.g. Phoenix, AZ"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="result_limit">Result Limit</label>
          <input
            id="result_limit"
            name="result_limit"
            type="text"
            value={fields.result_limit}
            onChange={handleChange}
            placeholder="e.g. 10"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="hours_old">Hours Old</label>
          <input
            id="hours_old"
            name="hours_old"
            type="text"
            value={fields.hours_old}
            onChange={handleChange}
            placeholder="e.g. 24"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="country">Country</label>
          <input
            id="country"
            name="country"
            type="text"
            value={fields.country}
            onChange={handleChange}
            placeholder="e.g. USA"
            className="border rounded px-2 py-1 w-full"
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1" htmlFor="minimum_score">Minimum Score</label>
          <input
            id="minimum_score"
            name="minimum_score"
            type="text"
            value={fields.minimum_score}
            onChange={handleChange}
            placeholder="e.g. 60"
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
                  jobs.map((job, idx) => {
                    const minScore = getMinimumScore();
                    const isBelowMin = job.score <= minScore;
                    // Download buttons are enabled only if job.curated is true
                    const isDownloadDisabled = !job.curated;
                    return (
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
                          {isBelowMin ? (
                            <span className="text-gray-400 italic">Score too low for curation</span>
                          ) : (
                            <>
                              <button
                                className="bg-blue-500 hover:bg-blue-700 text-white px-3 py-1 rounded mb-1"
                                onClick={() => handleDownloadResume(job.job_url, job.title)}
                                disabled={isDownloadDisabled}
                                style={isDownloadDisabled ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                              >
                                Download Resume
                              </button>
                              <button
                                className="bg-green-500 hover:bg-green-700 text-white px-3 py-1 rounded"
                                onClick={() => handleDownloadResume(job.job_url, job.title, true)}
                                disabled={isDownloadDisabled}
                                style={isDownloadDisabled ? { opacity: 0.5, cursor: 'not-allowed' } : {}}
                              >
                                Download Resume Pdf
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    );
                  })
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