import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BookOpen,
  Calendar,
  CheckCircle,
  Clock,
  FileText,
  GraduationCap,
  Megaphone,
  Plus,
  Search,
  Sparkles,
  UserCheck,
  Award,
  BarChart,
  Layers,
  Search as SearchIcon,
} from 'lucide-react';

import {
  fetchCurrentTerm,
  fetchCourseOfferings,
  fetchStudentAttendance,
  fetchStudentResults,
  fetchAnnouncements,
  createAnnouncement,
  fetchCampusEvents,
  fetchKnowledgeDocuments,
  performUnifiedSearch,
  recordAttendance,
  recordGrades,
  createAssessment,
} from '../lib/api';

export default function InstitutionalHub({ user }) {
  const [activeSubTab, setActiveSubTab] = useState('overview'); // 'overview', 'announcements', 'events', 'search', 'management'
  const [currentTerm, setCurrentTerm] = useState(null);
  const [offerings, setOfferings] = useState([]);
  const [attendanceData, setAttendanceData] = useState(null);
  const [resultsData, setResultsData] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [events, setEvents] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  // Form states for Faculty/Admin
  const [newAnnTitle, setNewAnnTitle] = useState('');
  const [newAnnContent, setNewAnnContent] = useState('');
  const [newAnnAudience, setNewAnnAudience] = useState('all');

  const [selectedOffering, setSelectedOffering] = useState('');
  const [attStdEnrollment, setAttStdEnrollment] = useState('');
  const [attStatus, setAttStatus] = useState('present');

  useEffect(() => {
    loadHubData();
  }, [user]);

  async function loadHubData() {
    setLoading(true);
    try {
      const term = await fetchCurrentTerm().catch(() => null);
      setCurrentTerm(term);

      const anns = await fetchAnnouncements().catch(() => ({ announcements: [] }));
      setAnnouncements(anns.announcements || []);

      const evts = await fetchCampusEvents().catch(() => ({ events: [] }));
      setEvents(evts.events || []);

      const offs = await fetchCourseOfferings().catch(() => ({ offerings: [] }));
      setOfferings(offs.offerings || []);

      const docs = await fetchKnowledgeDocuments().catch(() => ({ documents: [] }));
      setDocuments(docs.documents || []);

      if (user?.role === 'student' && user?.enrollment_no) {
        const att = await fetchStudentAttendance(user.enrollment_no).catch(() => null);
        setAttendanceData(att);

        const res = await fetchStudentResults(user.enrollment_no).catch(() => null);
        setResultsData(res);
      }
    } catch (e) {
      console.error('Failed to load institutional hub data:', e);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e) {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await performUnifiedSearch(searchQuery.trim());
      setSearchResults(res);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setIsSearching(false);
    }
  }

  async function handleCreateAnnouncement(e) {
    e.preventDefault();
    if (!newAnnTitle.trim() || !newAnnContent.trim()) return;
    try {
      await createAnnouncement({
        title: newAnnTitle,
        content: newAnnContent,
        audience: newAnnAudience,
      });
      setNewAnnTitle('');
      setNewAnnContent('');
      loadHubData();
    } catch (err) {
      alert('Failed to create announcement.');
    }
  }

  async function handleRecordAttendance(e) {
    e.preventDefault();
    if (!selectedOffering || !attStdEnrollment) return;
    try {
      await recordAttendance(selectedOffering, [
        { enrollment_no: attStdEnrollment.trim(), status: attStatus }
      ]);
      alert('Attendance recorded successfully!');
      setAttStdEnrollment('');
      loadHubData();
    } catch (err) {
      alert('Failed to record attendance.');
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-8 bg-[#080B14] text-slate-100">
      <div className="mx-auto max-w-[1500px] space-y-6">
        
        {/* Top Header Banner */}
        <div className="rounded-3xl border border-sky-500/20 bg-gradient-to-r from-sky-950/40 via-indigo-950/40 to-slate-900/60 p-6 shadow-2xl backdrop-blur-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-sky-400 font-extrabold text-xs uppercase tracking-widest">
                <Sparkles className="w-4 h-4" />
                <span>CampusMIND 2.0 Institutional Domain Platform</span>
              </div>
              <h2 className="mt-1 text-2xl md:text-3xl font-black text-white tracking-tight">
                {user?.role === 'student' ? 'Student Academic Intelligence' : user?.role === 'faculty' ? 'Faculty Academic Workstation' : 'Institutional Data Hub'}
              </h2>
              <p className="text-sm text-slate-400 mt-1">
                Active Term: <span className="font-bold text-sky-300">{currentTerm ? `${currentTerm.name} (${currentTerm.code})` : 'Fall 2024 Semester'}</span>
              </p>
            </div>

            {/* Quick Unified Search Bar */}
            <form onSubmit={handleSearch} className="relative min-w-[280px] md:min-w-[360px]">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search courses, notices, events, policies..."
                className="w-full rounded-2xl border border-sky-500/30 bg-slate-900/80 px-4 py-2.5 pl-10 text-xs font-semibold text-white placeholder-slate-500 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-500/20"
              />
              <SearchIcon className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
              <button
                type="submit"
                disabled={isSearching}
                className="absolute right-1.5 top-1.5 rounded-xl bg-sky-600 px-3 py-1 text-xs font-bold text-white hover:bg-sky-500 transition-all"
              >
                {isSearching ? '...' : 'Search'}
              </button>
            </form>
          </div>

          {/* Sub-Navigation Tabs */}
          <div className="mt-6 flex flex-wrap items-center gap-2 border-t border-slate-800/80 pt-4">
            <button
              onClick={() => { setActiveSubTab('overview'); setSearchResults(null); }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${activeSubTab === 'overview' && !searchResults ? 'bg-sky-500/20 border border-sky-400/40 text-sky-300' : 'text-slate-400 hover:text-white'}`}
            >
              <BarChart className="w-4 h-4" />
              <span>Overview</span>
            </button>
            <button
              onClick={() => { setActiveSubTab('announcements'); setSearchResults(null); }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${activeSubTab === 'announcements' && !searchResults ? 'bg-sky-500/20 border border-sky-400/40 text-sky-300' : 'text-slate-400 hover:text-white'}`}
            >
              <Megaphone className="w-4 h-4" />
              <span>Announcements</span>
            </button>
            <button
              onClick={() => { setActiveSubTab('events'); setSearchResults(null); }}
              className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${activeSubTab === 'events' && !searchResults ? 'bg-sky-500/20 border border-sky-400/40 text-sky-300' : 'text-slate-400 hover:text-white'}`}
            >
              <Calendar className="w-4 h-4" />
              <span>Campus Events</span>
            </button>
            {user?.role !== 'student' && (
              <button
                onClick={() => { setActiveSubTab('management'); setSearchResults(null); }}
                className={`flex items-center gap-2 rounded-xl px-4 py-2 text-xs font-bold transition-all ${activeSubTab === 'management' && !searchResults ? 'bg-purple-500/20 border border-purple-400/40 text-purple-300' : 'text-slate-400 hover:text-white'}`}
              >
                <UserCheck className="w-4 h-4" />
                <span>Academic Actions</span>
              </button>
            )}
          </div>
        </div>

        {/* Search Results Overlay */}
        {searchResults && (
          <div className="rounded-3xl border border-sky-500/30 bg-slate-900/90 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white">
                Search Results for "{searchResults.query}"
              </h3>
              <button
                onClick={() => setSearchResults(null)}
                className="text-xs font-bold text-slate-400 hover:text-white"
              >
                Clear Search
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Courses */}
              <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-sky-400 mb-2">Courses ({searchResults.courses.length})</h4>
                {searchResults.courses.length === 0 ? <p className="text-xs text-slate-500">No matching courses.</p> : (
                  <div className="space-y-2">
                    {searchResults.courses.map((c) => (
                      <div key={c.id} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                        <span className="font-extrabold text-sky-300">{c.code}:</span> {c.title} ({c.credits} Credits)
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Announcements */}
              <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2">Announcements ({searchResults.announcements.length})</h4>
                {searchResults.announcements.length === 0 ? <p className="text-xs text-slate-500">No matching announcements.</p> : (
                  <div className="space-y-2">
                    {searchResults.announcements.map((a) => (
                      <div key={a.id} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                        <div className="font-bold text-amber-200">{a.title}</div>
                        <div className="text-slate-400 mt-1">{a.snippet}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Events */}
              <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-purple-400 mb-2">Events ({searchResults.events.length})</h4>
                {searchResults.events.length === 0 ? <p className="text-xs text-slate-500">No matching events.</p> : (
                  <div className="space-y-2">
                    {searchResults.events.map((ev) => (
                      <div key={ev.id} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                        <div className="font-bold text-purple-300">{ev.title}</div>
                        <div className="text-slate-400">{ev.location}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Documents */}
              <div className="rounded-2xl bg-slate-950/60 p-4 border border-slate-800">
                <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">Documents ({searchResults.documents.length})</h4>
                {searchResults.documents.length === 0 ? <p className="text-xs text-slate-500">No matching documents.</p> : (
                  <div className="space-y-2">
                    {searchResults.documents.map((d) => (
                      <div key={d.id} className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs">
                        <div className="font-bold text-emerald-300">{d.title}</div>
                        <div className="text-slate-400">{d.file_path}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Main Content Area */}
        {activeSubTab === 'overview' && !searchResults && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Student View Cards */}
            {user?.role === 'student' && (
              <>
                {/* Attendance Summary Card */}
                <div className="rounded-3xl border border-sky-500/20 bg-slate-900/60 p-6 shadow-xl space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-extrabold uppercase tracking-wider text-sky-400 flex items-center gap-2">
                      <Clock className="w-4 h-4" />
                      <span>Attendance Record</span>
                    </h3>
                    <span className="rounded-full bg-sky-500/20 px-3 py-1 text-xs font-extrabold text-sky-300">
                      {attendanceData?.summary ? `${attendanceData.summary.attendance_pct}%` : '100%'}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Total Classes Conducted:</span>
                      <span className="font-bold text-white">{attendanceData?.summary?.total_classes || 10}</span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Classes Attended:</span>
                      <span className="font-bold text-emerald-400">{attendanceData?.summary?.attended_classes || 10}</span>
                    </div>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2.5">
                    <div
                      className="bg-gradient-to-r from-sky-400 to-emerald-400 h-2.5 rounded-full"
                      style={{ width: `${attendanceData?.summary?.attendance_pct || 90}%` }}
                    />
                  </div>
                </div>

                {/* Academic Performance Card */}
                <div className="rounded-3xl border border-purple-500/20 bg-slate-900/60 p-6 shadow-xl space-y-4 lg:col-span-2">
                  <h3 className="text-sm font-extrabold uppercase tracking-wider text-purple-400 flex items-center gap-2">
                    <Award className="w-4 h-4" />
                    <span>Academic Assessment Results</span>
                  </h3>
                  {resultsData?.results && resultsData.results.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs">
                        <thead>
                          <tr className="border-b border-slate-800 text-slate-400">
                            <th className="pb-2">Assessment</th>
                            <th className="pb-2">Type</th>
                            <th className="pb-2">Obtained Marks</th>
                            <th className="pb-2">Grade</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60">
                          {resultsData.results.map((r) => (
                            <tr key={r.id} className="text-slate-200">
                              <td className="py-2.5 font-bold">{r.assessment_title}</td>
                              <td className="py-2.5 uppercase text-slate-400">{r.assessment_type}</td>
                              <td className="py-2.5 font-extrabold text-sky-300">{r.obtained_marks} / {r.max_marks}</td>
                              <td className="py-2.5 font-bold text-emerald-400">{r.grade || 'A'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-500 italic">No published assessment grades found for current term.</p>
                  )}
                </div>
              </>
            )}

            {/* Course Offerings Overview */}
            <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl lg:col-span-3 space-y-4">
              <h3 className="text-sm font-extrabold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-sky-400" />
                <span>Active Course Offerings ({offerings.length})</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {offerings.slice(0, 6).map((o) => (
                  <div key={o.id} className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4 space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="rounded-lg bg-sky-500/10 px-2.5 py-1 text-xs font-bold text-sky-400 border border-sky-500/20">{o.course_code}</span>
                      <span className="text-[10px] text-slate-500 font-bold uppercase">{o.section} Section</span>
                    </div>
                    <h4 className="text-sm font-bold text-white line-clamp-1">{o.course_title}</h4>
                    <div className="text-xs text-slate-400">
                      Instructor: <span className="text-slate-200">{o.faculty_name || 'Faculty Member'}</span>
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono">{o.schedule || 'Schedule TBA'} • {o.room || 'Main Block'}</div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* Announcements Tab */}
        {activeSubTab === 'announcements' && !searchResults && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Megaphone className="w-5 h-5 text-amber-400" />
              <span>Official Institutional Notices</span>
            </h3>
            <div className="grid grid-cols-1 gap-4">
              {announcements.map((a) => (
                <div key={a.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-base font-bold text-amber-200">{a.title}</h4>
                    <span className="rounded-full bg-amber-500/10 px-3 py-1 text-[11px] font-bold text-amber-400 border border-amber-500/20">
                      {a.priority.toUpperCase()} PRIORITY
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{a.content}</p>
                  <div className="text-[11px] text-slate-500 pt-2 flex items-center gap-4">
                    <span>Target Audience: <strong className="text-slate-400">{a.audience}</strong></span>
                    <span>Published: <strong className="text-slate-400">{new Date(a.created_at).toLocaleDateString()}</strong></span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Events Tab */}
        {activeSubTab === 'events' && !searchResults && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Calendar className="w-5 h-5 text-purple-400" />
              <span>Upcoming Campus Events</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {events.map((ev) => (
                <div key={ev.id} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="rounded-lg bg-purple-500/10 px-2.5 py-1 text-xs font-bold text-purple-400 border border-purple-500/20 uppercase">{ev.category}</span>
                    <span className="text-xs text-slate-400 font-semibold">{ev.location}</span>
                  </div>
                  <h4 className="text-base font-bold text-white">{ev.title}</h4>
                  <p className="text-xs text-slate-400">{ev.description}</p>
                  <div className="pt-2 flex items-center justify-between border-t border-slate-800 text-xs">
                    <span className="text-slate-500">{new Date(ev.start_time).toLocaleString()}</span>
                    <button
                      onClick={() => registerForEvent(ev.id).then(() => alert('Registered!'))}
                      className="rounded-xl bg-purple-600 px-3.5 py-1.5 font-bold text-white hover:bg-purple-500 transition-all"
                    >
                      Register Now
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Faculty / Admin Management Tab */}
        {activeSubTab === 'management' && user?.role !== 'student' && !searchResults && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Create Announcement Form */}
            <div className="rounded-3xl border border-amber-500/20 bg-slate-900/60 p-6 space-y-4">
              <h3 className="text-base font-extrabold text-amber-300 flex items-center gap-2">
                <Plus className="w-4 h-4" />
                <span>Publish Announcement</span>
              </h3>
              <form onSubmit={handleCreateAnnouncement} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Notice Title</label>
                  <input
                    type="text"
                    value={newAnnTitle}
                    onChange={(e) => setNewAnnTitle(e.target.value)}
                    placeholder="Enter announcement title"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Target Audience</label>
                  <select
                    value={newAnnAudience}
                    onChange={(e) => setNewAnnAudience(e.target.value)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-amber-400"
                  >
                    <option value="all">All Campus Users</option>
                    <option value="students">Students Only</option>
                    <option value="faculty">Faculty Members Only</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Notice Content</label>
                  <textarea
                    rows={3}
                    value={newAnnContent}
                    onChange={(e) => setNewAnnContent(e.target.value)}
                    placeholder="Enter full notice body text"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-amber-400"
                    required
                  />
                </div>
                <button
                  type="submit"
                  className="w-full rounded-xl bg-amber-600 py-2.5 font-bold text-white hover:bg-amber-500 transition-all"
                >
                  Publish Notice
                </button>
              </form>
            </div>

            {/* Quick Attendance Marking Form */}
            <div className="rounded-3xl border border-sky-500/20 bg-slate-900/60 p-6 space-y-4">
              <h3 className="text-base font-extrabold text-sky-300 flex items-center gap-2">
                <CheckCircle className="w-4 h-4" />
                <span>Session Attendance Marker</span>
              </h3>
              <form onSubmit={handleRecordAttendance} className="space-y-3 text-xs">
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Course Offering</label>
                  <select
                    value={selectedOffering}
                    onChange={(e) => setSelectedOffering(e.target.value)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-sky-400"
                    required
                  >
                    <option value="">Select Offering</option>
                    {offerings.map((o) => (
                      <option key={o.id} value={o.id}>{o.course_code}: {o.course_title} ({o.section})</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Student Enrollment Number</label>
                  <input
                    type="text"
                    value={attStdEnrollment}
                    onChange={(e) => setAttStdEnrollment(e.target.value)}
                    placeholder="e.g. 2024IFHE001"
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-sky-400"
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-400 font-semibold mb-1">Attendance Status</label>
                  <select
                    value={attStatus}
                    onChange={(e) => setAttStatus(e.target.value)}
                    className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3.5 py-2 text-white focus:outline-none focus:border-sky-400"
                  >
                    <option value="present">Present</option>
                    <option value="absent">Absent</option>
                    <option value="late">Late</option>
                    <option value="excused">Excused</option>
                  </select>
                </div>
                <button
                  type="submit"
                  className="w-full rounded-xl bg-sky-600 py-2.5 font-bold text-white hover:bg-sky-500 transition-all"
                >
                  Submit Attendance Entry
                </button>
              </form>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
