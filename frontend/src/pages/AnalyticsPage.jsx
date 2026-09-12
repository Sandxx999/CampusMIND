import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  BookOpen,
  Calendar,
  CheckCircle2,
  GraduationCap,
  Layers,
  Loader2,
  RefreshCw,
  ShieldCheck,
  UserCheck,
  Users,
} from 'lucide-react';
import {
  fetchStudentAnalyticsMe,
  fetchFacultyOfferingAnalytics,
  fetchAdminAnalyticsOverview,
  fetchCourseOfferings,
} from '../lib/api';
import RiskIndicator from '../components/analytics/RiskIndicator';
import AttendanceSummary from '../components/analytics/AttendanceSummary';
import PerformanceSummary from '../components/analytics/PerformanceSummary';
import RecommendationCard from '../components/analytics/RecommendationCard';
import CoursePerformance from '../components/analytics/CoursePerformance';
import AnalyticsEmptyState from '../components/analytics/AnalyticsEmptyState';

export default function AnalyticsPage({ user }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [studentSummary, setStudentSummary] = useState(null);
  const [facultyOfferings, setFacultyOfferings] = useState([]);
  const [selectedOfferingId, setSelectedOfferingId] = useState('');
  const [facultyAnalytics, setFacultyAnalytics] = useState(null);
  const [adminOverview, setAdminOverview] = useState(null);

  useEffect(() => {
    loadAnalyticsData();
  }, [user]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (user.role === 'student') {
        const data = await fetchStudentAnalyticsMe();
        setStudentSummary(data);
      } else if (user.role === 'faculty') {
        const offeringsData = await fetchCourseOfferings();
        const offerings = offeringsData.offerings || [];
        setFacultyOfferings(offerings);
        if (offerings.length > 0) {
          const firstId = offerings[0].id;
          setSelectedOfferingId(firstId);
          const fData = await fetchFacultyOfferingAnalytics(firstId);
          setFacultyAnalytics(fData);
        }
      } else if (user.role === 'admin') {
        const aData = await fetchAdminAnalyticsOverview();
        setAdminOverview(aData);
      }
    } catch (err) {
      console.error('Error loading analytics:', err);
      setError(err.response?.data?.detail || 'Failed to load academic analytics data.');
    } finally {
      setLoading(false);
    }
  };

  const handleOfferingChange = async (offeringId) => {
    setSelectedOfferingId(offeringId);
    setLoading(true);
    try {
      const fData = await fetchFacultyOfferingAnalytics(offeringId);
      setFacultyAnalytics(fData);
    } catch (err) {
      console.error('Error changing offering:', err);
      setError('Failed to load offering analytics.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[#080B14] px-4 py-6 md:px-8">
      <div className="mx-auto max-w-[1700px] space-y-6">
        {/* Header Title Section */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-4">
          <div>
            <h2 className="font-display text-2xl font-black tracking-tight text-white md:text-3xl">
              Academic Analytics & Intelligence
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic, explainable performance & risk insights derived from canonical campus records.
            </p>
          </div>
          <button
            onClick={loadAnalyticsData}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-xs font-bold text-slate-200 transition-all hover:bg-white/10"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin text-sky-400' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="flex h-64 items-center justify-center">
            <div className="flex items-center gap-3 text-sky-400">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span className="font-display text-sm font-semibold">Computing academic analytics...</span>
            </div>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 p-5 text-rose-300 backdrop-blur-xl">
            <h4 className="font-display font-bold">Analytics Computation Alert</h4>
            <p className="mt-1 text-xs">{error}</p>
          </div>
        )}

        {/* STUDENT ANALYTICS VIEW */}
        {!loading && !error && user.role === 'student' && (
          <div className="space-y-6">
            {studentSummary ? (
              <>
                {/* Risk Analysis Banner */}
                <RiskIndicator riskAnalysis={studentSummary.risk_analysis} />

                {/* Performance Summary Cards */}
                <PerformanceSummary performanceSummary={studentSummary.performance_summary} />

                {/* Attendance Breakdown */}
                <AttendanceSummary attendanceSummary={studentSummary.attendance_summary} />

                {/* Course Performance Detail & Recommendations */}
                <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
                  <CoursePerformance
                    performanceByCourse={studentSummary.performance_summary?.performance_by_course}
                  />
                  <RecommendationCard recommendations={studentSummary.recommendations} />
                </div>
              </>
            ) : (
              <AnalyticsEmptyState
                title="No Academic Data"
                description="Student profile records are not yet linked for this account."
              />
            )}
          </div>
        )}

        {/* FACULTY ANALYTICS VIEW */}
        {!loading && !error && user.role === 'faculty' && (
          <div className="space-y-6">
            {facultyOfferings.length > 0 && (
              <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-900/60 p-4 backdrop-blur-xl">
                <label className="text-xs font-bold text-slate-300">Select Section Offering:</label>
                <select
                  value={selectedOfferingId}
                  onChange={(e) => handleOfferingChange(e.target.value)}
                  className="rounded-xl border border-white/20 bg-slate-800 px-3 py-1.5 text-xs text-white outline-none focus:border-sky-500"
                >
                  {facultyOfferings.map((off) => (
                    <option key={off.id} value={off.id}>
                      {off.course_code} - {off.course_title} (Section {off.section})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {facultyAnalytics ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Total Enrolled</span>
                    <span className="font-display text-2xl font-black text-sky-400">
                      {facultyAnalytics.total_enrolled}
                    </span>
                  </div>
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Section Avg Attendance</span>
                    <span className="font-display text-2xl font-black text-emerald-400">
                      {facultyAnalytics.average_attendance_pct}%
                    </span>
                  </div>
                  <div className="rounded-2xl border border-indigo-500/20 bg-indigo-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Section Avg Assessment Score</span>
                    <span className="font-display text-2xl font-black text-indigo-300">
                      {facultyAnalytics.average_assessment_pct}%
                    </span>
                  </div>
                </div>

                {/* At Risk Students List */}
                {facultyAnalytics.students_requiring_attention &&
                facultyAnalytics.students_requiring_attention.length > 0 ? (
                  <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-5 backdrop-blur-xl">
                    <h4 className="font-display font-bold text-rose-300 mb-3">
                      Students Requiring Academic Attention ({facultyAnalytics.students_requiring_attention.length})
                    </h4>
                    <div className="divide-y divide-white/10">
                      {facultyAnalytics.students_requiring_attention.map((s, idx) => (
                        <div key={idx} className="flex justify-between items-center py-2.5 text-xs">
                          <div>
                            <span className="font-bold text-slate-100">{s.student_name}</span>
                            <span className="ml-2 text-slate-400">({s.enrollment_no})</span>
                          </div>
                          <div className="text-right">
                            <span className="font-bold text-rose-400">{s.reason}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs text-emerald-300 backdrop-blur-xl">
                    All students in this section are currently within safe attendance thresholds.
                  </div>
                )}
              </div>
            ) : (
              <AnalyticsEmptyState
                title="No Section Offering Selected"
                description="Select a course offering section assigned to your faculty profile."
              />
            )}
          </div>
        )}

        {/* ADMIN ANALYTICS VIEW */}
        {!loading && !error && user.role === 'admin' && (
          <div className="space-y-6">
            {adminOverview ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                  <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Total Enrolled Students</span>
                    <span className="font-display text-2xl font-black text-sky-400">
                      {adminOverview.total_students}
                    </span>
                  </div>
                  <div className="rounded-2xl border border-purple-500/20 bg-purple-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Faculty Members</span>
                    <span className="font-display text-2xl font-black text-purple-300">
                      {adminOverview.total_faculty}
                    </span>
                  </div>
                  <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Institutional Avg CGPA</span>
                    <span className="font-display text-2xl font-black text-emerald-400">
                      {adminOverview.average_cgpa.toFixed(2)}
                    </span>
                  </div>
                  <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 backdrop-blur-xl">
                    <span className="block text-xs font-semibold text-slate-300">Students Below Threshold</span>
                    <span className="font-display text-2xl font-black text-amber-400">
                      {adminOverview.students_below_attendance_threshold}
                    </span>
                  </div>
                </div>

                <div className="rounded-2xl border border-white/10 bg-slate-900/60 p-5 backdrop-blur-xl">
                  <h4 className="font-display font-bold text-slate-100 mb-2">Institutional Academic Risk Distribution</h4>
                  <p className="text-xs text-slate-400">
                    Students in Critical Attendance Risk (&lt;60%):{' '}
                    <strong className="text-rose-400">{adminOverview.students_in_critical_risk}</strong> | Students with Active Backlogs:{' '}
                    <strong className="text-amber-400">{adminOverview.students_with_backlogs}</strong>
                  </p>
                </div>
              </div>
            ) : (
              <AnalyticsEmptyState
                title="Institutional Analytics Unavailable"
                description="Unable to compute institutional overview statistics."
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
