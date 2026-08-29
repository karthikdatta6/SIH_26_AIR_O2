import { HashRouter, Routes, Route } from "react-router-dom";
import { Hero } from "./components/hero/Hero";
import { DelhiMap } from "./components/map/DelhiMap";
import { StationDashboard } from "./components/station/StationDashboard";
import { PageTransitionProvider } from "./lib/PageTransition";

function App() {
  return (
    <HashRouter>
      <PageTransitionProvider>
        <div className="crt-vignette" />
        <div className="crt-layer" />
        <Routes>
          <Route path="/" element={<Hero />} />
          <Route path="/network" element={<DelhiMap />} />
          <Route path="/station/:stationId" element={<StationDashboard />} />
        </Routes>
      </PageTransitionProvider>
    </HashRouter>
  );
}

export default App;
