import React, { useState } from 'react';

const AgentRunner: React.FC = () => {
  const [fields, setFields] = useState({
    field1: '',
    field2: '',
    field3: '',
    field4: '',
    field5: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [reviseMsg, setReviseMsg] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFields({
      ...fields,
      [e.target.name]: e.target.value,
    });
  };

  const handleAutomat = async () => {
    try {
      setIsLoading(true);
      setReviseMsg('');

      const params = new URLSearchParams({
        search_term: fields.field1 || "software engineer",
        location: fields.field2 || "Phoenix, AZ",
        results_wanted: fields.field3 || "10",
        hours_old: fields.field4 || "24",
        country_indeed: fields.field5 || "USA",
      }).toString();
      const res = await fetch(`http://localhost:3003/api/automate?${params}`);

      if (!res.ok) throw new Error(`Error: ${res.status}`);

    //   The automate endpoint returns a single async result, not a stream
      const result = await res.json();

    //   You may need to adjust this depending on the response structure
    //   For example, if result is { message: "..." }
      if (typeof result === 'string') {
        setReviseMsg(result);
      } else if (result && result.message) {
        setReviseMsg(result.message);
      } else {
        setReviseMsg(JSON.stringify(result));
      }
    } catch (err) {
      console.error('Post error:', err);
      setReviseMsg('Error: ' + (err as Error).message);
    } finally {
      setIsLoading(false);
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
        <textarea
          value={reviseMsg}
          readOnly
          placeholder={isLoading ? "Processing..." : "Result will appear here..."}
          className="w-full h-full p-2 border border-gray-300 rounded resize-none overflow-auto"
          style={{ minHeight: '300px', overflow: 'auto' }}
        />
      </div>
    </div>
  );
};
export default AgentRunner;