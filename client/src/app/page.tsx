"use client";

import React from 'react';
import SendMessage from './components/SendMessage';
import { Tab, Tabs, TabList, TabPanel } from 'react-tabs';
import 'react-tabs/style/react-tabs.css';
import AgentRunner from './components/AgentRunner';

export default function Home() {
  return (
    <div>
      <main>
        <Tabs>
          <TabList>
            <Tab>Send Message</Tab>
            <Tab>Agent Runner</Tab>
          </TabList>

          <TabPanel>
            <SendMessage />
          </TabPanel>
          <TabPanel>
            <AgentRunner />
          </TabPanel>
        </Tabs>
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
      </footer>
    </div>
  );
}
