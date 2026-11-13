import React, { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import { Navbar } from "./components/Navbar";
import { AuthModal } from "./components/AuthModal";
import { PlaygroundPage } from "./pages/PlaygroundPage";
import { ChallengesPage } from "./pages/ChallengesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AchievementsPage } from "./pages/AchievementsPage";
import { AcademyPage, AcademyTarget } from "./pages/AcademyPage";
import { RoadmapPage } from "./pages/RoadmapPage";
import { MemoryPage } from "./pages/MemoryPage";
import { LandingPage } from "./pages/LandingPage";
import "./App.css";
import "./learning.css";
import "./game.css";

const GUARDED_TABS = ["roadmap", "memory", "dashboard", "achievements"];

const AppContent: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>(() =>
    // first-time and signed-out visitors start on the landing page
    localStorage.getItem("mentor_token") ? "playground" : "landing"
  );
  const { isAuthenticated } = useAuth();
  const [selectedChallengeId, setSelectedChallengeId] = useState<string | null>("ch_sum_list");
  const [isAuthOpen, setIsAuthOpen] = useState<boolean>(false);
  const [academyTarget, setAcademyTarget] = useState<AcademyTarget>({ view: "courses" });

  const handleSelectChallenge = (id: string) => {
    setSelectedChallengeId(id);
    setCurrentTab("playground");
  };

  const openAcademy = (target: AcademyTarget) => {
    setAcademyTarget(target);
    setCurrentTab("academy");
  };

  /** Shared navigation for recovery suggestions, roadmap days and dashboard cards. */
  const navigateTo = (targetType: string, targetId: string) => {
    if (targetType === "challenge") handleSelectChallenge(targetId);
    else if (targetType === "course_task") openAcademy({ view: "task", taskId: targetId });
    else if (targetType === "course_lesson") openAcademy({ view: "lesson", lessonId: targetId });
  };

  // Signing in from the landing page drops you on the course path.
  useEffect(() => {
    if (isAuthenticated && currentTab === "landing") setCurrentTab("academy");
  }, [isAuthenticated]);

  if (currentTab === "landing") {
    return (
      <div className="app-container">
        <LandingPage
          onOpenTab={(tab) => (GUARDED_TABS.includes(tab) && !isAuthenticated ? setIsAuthOpen(true) : setCurrentTab(tab))}
          onOpenAuth={() => setIsAuthOpen(true)}
        />
        <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Global Navigation */}
      <Navbar
        currentTab={currentTab}
        setCurrentTab={(tab) => {
          if (tab === "academy") setAcademyTarget({ view: "courses" });
          setCurrentTab(tab);
        }}
        onOpenAuth={() => setIsAuthOpen(true)}
      />

      {/* Main Routed Page */}
      <main className="app-content">
        {currentTab === "playground" && (
          <PlaygroundPage
            initialChallengeId={selectedChallengeId}
            onOpenGenerator={() => setCurrentTab("challenges")}
            onOpenAuth={() => setIsAuthOpen(true)}
            onNavigate={navigateTo}
          />
        )}

        {currentTab === "challenges" && (
          <ChallengesPage onSelectChallenge={handleSelectChallenge} />
        )}

        {currentTab === "academy" && (
          <AcademyPage
            target={academyTarget}
            onNavigate={setAcademyTarget}
            onOpenAuth={() => setIsAuthOpen(true)}
            onOpenChallenge={handleSelectChallenge}
          />
        )}

        {currentTab === "roadmap" && (
          <RoadmapPage
            onOpenCourseTask={(id) => openAcademy({ view: "task", taskId: id })}
            onOpenLesson={(id) => openAcademy({ view: "lesson", lessonId: id })}
            onOpenChallenge={handleSelectChallenge}
          />
        )}

        {currentTab === "memory" && <MemoryPage />}

        {currentTab === "dashboard" && (
          <DashboardPage
            onSelectChallenge={handleSelectChallenge}
            onOpenPlayground={() => setCurrentTab("playground")}
            onOpenRoadmap={() => setCurrentTab("roadmap")}
            onOpenCourse={(slug) => openAcademy({ view: "course", slug })}
            onNavigate={navigateTo}
          />
        )}

        {currentTab === "achievements" && <AchievementsPage />}
      </main>

      {/* Auth Modal */}
      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
