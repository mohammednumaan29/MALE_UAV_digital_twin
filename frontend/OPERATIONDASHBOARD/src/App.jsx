import React, { useState } from 'react';

import Header from './components/Header';
import Sidebar from './components/Sidebar';

import OverviewView from './views/OverviewView';
import TelemetryView from './views/TelemetryView';
import DiagnosticsView from './views/DiagnosticsView';
import MissionView from './views/MissionView';
import SimulationView from './views/SimulationView';
import ReportsView from './views/ReportsView';


/* ============================================================
   APP
   ============================================================ */

export default function App() {

  /* ==========================================================
     STATE
     ========================================================== */

  const [activeView, setActiveView] =
    useState('overview');


  const [sidebarCollapsed, setSidebarCollapsed] =
    useState(false);


  /* ==========================================================
     NAVIGATION
     ========================================================== */

  const handleNavigate = (view) => {

    setActiveView(view);

  };


  /* ==========================================================
     SIDEBAR TOGGLE
     ========================================================== */

  const handleMenuClick = () => {

    setSidebarCollapsed(
      (previous) => !previous
    );

  };


  /* ==========================================================
     RENDER ACTIVE VIEW
     ========================================================== */

  const renderView = () => {

    switch (activeView) {


      /* ------------------------------------------------------
         OVERVIEW
         ------------------------------------------------------ */

      case 'overview':

        return (
          <OverviewView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         TELEMETRY
         ------------------------------------------------------ */

      case 'telemetry':

        return (
          <TelemetryView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         DIAGNOSTICS
         ------------------------------------------------------ */

      case 'diagnostics':

        return (
          <DiagnosticsView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         MISSION
         ------------------------------------------------------ */

      case 'mission':

        return (
          <MissionView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         SIMULATION
         ------------------------------------------------------ */

      case 'simulation':

        return (
          <SimulationView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         REPORTS
         ------------------------------------------------------ */

      case 'reports':

        return (
          <ReportsView
            onNavigate={handleNavigate}
          />
        );


      /* ------------------------------------------------------
         DEFAULT
         ------------------------------------------------------ */

      default:

        return (
          <OverviewView
            onNavigate={handleNavigate}
          />
        );

    }

  };


  /* ==========================================================
     LAYOUT
     ========================================================== */

  return (

    <div className="
      min-h-screen
      bg-slate-50
      text-slate-900
    ">


      {/* ======================================================
          SIDEBAR
          ====================================================== */}

      <Sidebar
        activeView={activeView}
        onNavigate={handleNavigate}
        collapsed={sidebarCollapsed}
        onToggle={handleMenuClick}
      />


      {/* ======================================================
          MAIN AREA
          ====================================================== */}

      <div
        className={`
          min-h-screen
          transition-[padding-left]
          duration-200

          ${
            sidebarCollapsed
              ? 'pl-[68px]'
              : 'pl-[220px]'
          }
        `}
      >


        {/* ====================================================
            HEADER
            ==================================================== */}

        <Header
          onMenuClick={handleMenuClick}
          notifications={2}
          userInitials="AK"
        />


        {/* ====================================================
            PAGE CONTENT
            ==================================================== */}

        <main className="
          min-h-[calc(100vh-72px)]
          overflow-x-hidden
        ">

          {renderView()}

        </main>

      </div>

    </div>

  );

}