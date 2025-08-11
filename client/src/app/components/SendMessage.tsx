import React, { useState } from 'react';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import FileUploader from './FileUploader';

const SendMessage = () => {
  const [inputText, setInputText] = useState('');
  const [responseMsg, setResponseMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [reviseMsg, setReviseMsg] = useState('');
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (index: number) => {
    setTabIndex(index);
  };

  const handlePost = async () => {
    try {
      setIsLoading(true);
      setResponseMsg(''); // Clear previous response
      setReviseMsg('');
      setTabIndex(0);

      const res = await fetch('http://localhost:3003/api/send_message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ text: inputText }),
      });

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      // Handle streaming response
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix

            if (data === '[DONE]') {
              break;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                setResponseMsg(prev => prev + parsed.content);
              }
            } catch (err) {
              // Skip invalid JSON
              console.error('Post error:', err);
            }
          }
        }
      }
    } catch (err) {
      console.error('Post error:', err);
      setResponseMsg('Error: ' + (err as Error).message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRevise = async () => {
    try {
      setIsLoading(true);
      setReviseMsg('');
      setTabIndex(1);

      const res = await fetch('http://localhost:3003/api/revise_resume');

      if (!res.ok) throw new Error(`Error: ${res.status}`);

      // Handle streaming response
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6); // Remove 'data: ' prefix

            if (data === '[DONE]') {
              break;
            }

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                setReviseMsg(prev => prev + parsed.content);
              }
            } catch (err) {
              // Skip invalid JSON
              console.error('Post error:', err);
            }
          }
        }
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
      {/* Left Column */}
      <div className="w-1/4 p-2 max-w-md mx-auto">
        <div className="flex gap-2">
          <div>
            <FileUploader />
            <button
              onClick={handlePost}
              disabled={isLoading}
              className={`px-4 py-2 rounded ${isLoading
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                : 'bg-gray-600 hover:bg-gray-400 text-white'
                }`}
              style={{ marginRight: '4px' }}
            >
              {isLoading ? 'Processing...' : 'Compare To Resume'}
            </button>
            <button
              onClick={handleRevise}
              disabled={isLoading}
              className={`px-4 py-2 rounded ${isLoading
                ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                : 'bg-gray-600 hover:bg-gray-400 text-white'
                }`}
            >
              {isLoading ? 'Processing...' : 'Revise Resume'}
            </button>
          </div>
        </div>
        <div style={{ height: '6px' }} />
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          placeholder="Enter your job description here..."
          className="w-full h-3/4 p-3 border border-gray-300 rounded resize-none"
        />

      </div>
      <div className="w-3/4 p-6">
        <Tabs
          selectedIndex={tabIndex}
          onSelect={handleTabChange}
        >
          <TabList>
            <Tab>Compare Result</Tab>
            <Tab>Revised Resume</Tab>
          </TabList>
          <TabPanel>
            <textarea
              value={responseMsg}
              readOnly
              placeholder={isLoading ? "Generating response..." : "Response will appear here..."}
              className="w-full h-[calc(100vh-100px)] p-2 border border-gray-300 rounded resize-none overflow-auto"
              style={{ overflow: 'auto' }}
            />
          </TabPanel>
          <TabPanel>
            <textarea
              value={reviseMsg}
              readOnly
              placeholder={isLoading ? "Generating response..." : "Revised resume will appear here..."}
              className="w-full h-[calc(100vh-100px)] p-2 border border-gray-300 rounded resize-none overflow-auto"
              style={{ overflow: 'auto' }}
            />
          </TabPanel>
        </Tabs>
      </div>
    </div >
  );
};

export default SendMessage