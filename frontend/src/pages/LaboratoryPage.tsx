import React, { useEffect, useState } from 'react';
import { BookOpen, Plus, Search, Tag, TestTubes } from 'lucide-react';
import api from '../lib/axios';
import { LaboratoryTest, TestCategory } from '../types';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';

export const LaboratoryPage: React.FC = () => {
  const [tests, setTests] = useState<LaboratoryTest[]>([]);
  const [categories, setCategories] = useState<TestCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  // New Test Modal
  const [isTestModalOpen, setIsTestModalOpen] = useState(false);
  const [testCode, setTestCode] = useState('');
  const [testName, setTestName] = useState('');
  const [testCatId, setTestCatId] = useState('');
  const [testUnit, setTestUnit] = useState('');
  const [testDesc, setTestDesc] = useState('');
  const [submittingTest, setSubmittingTest] = useState(false);

  // New Reference Range Modal
  const [selectedTestForRange, setSelectedTestForRange] = useState<LaboratoryTest | null>(null);
  const [lowerLimit, setLowerLimit] = useState('');
  const [upperLimit, setUpperLimit] = useState('');
  const [rangeSource, setRangeSource] = useState('');
  const [submittingRange, setSubmittingRange] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [tRes, cRes] = await Promise.all([
        api.get('/laboratory/tests', {
          params: { search: search.trim() || undefined, category_id: selectedCategory || undefined },
        }),
        api.get('/laboratory/categories'),
      ]);
      setTests(tRes.data);
      setCategories(cRes.data);
      if (cRes.data.length > 0 && !testCatId) {
        setTestCatId(cRes.data[0].id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, selectedCategory]);

  const handleCreateTest = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingTest(true);
    try {
      await api.post('/laboratory/tests', {
        test_code: testCode.trim().toUpperCase(),
        name: testName.trim(),
        category_id: testCatId,
        measurement_unit: testUnit.trim() || null,
        description: testDesc.trim() || null,
        result_type: 'numeric',
      });
      setIsTestModalOpen(false);
      setTestCode('');
      setTestName('');
      setTestUnit('');
      setTestDesc('');
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create test definition.');
    } finally {
      setSubmittingTest(false);
    }
  };

  const handleCreateRange = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTestForRange) return;
    setSubmittingRange(true);
    try {
      await api.post('/laboratory/reference-ranges', {
        test_id: selectedTestForRange.id,
        applicable_sex: 'all',
        lower_limit: lowerLimit ? parseFloat(lowerLimit) : null,
        upper_limit: upperLimit ? parseFloat(upperLimit) : null,
        source: rangeSource.trim(),
      });
      setSelectedTestForRange(null);
      setLowerLimit('');
      setUpperLimit('');
      setRangeSource('');
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add reference range.');
    } finally {
      setSubmittingRange(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100">Laboratory Test Catalogue</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Configurable clinical assays, measurement units, and accredited reference intervals.
          </p>
        </div>
        <Button onClick={() => setIsTestModalOpen(true)} className="gap-2">
          <Plus className="w-4 h-4" /> Define Laboratory Test
        </Button>
      </div>

      <Card>
        {/* Filter bar */}
        <div className="flex flex-col sm:flex-row gap-3 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by test code or name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-1.5 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Tests Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 border-b border-slate-200 dark:border-slate-700 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 font-semibold">Test Code</th>
                <th className="py-2.5 px-3 font-semibold">Test Name</th>
                <th className="py-2.5 px-3 font-semibold">Category</th>
                <th className="py-2.5 px-3 font-semibold">Units</th>
                <th className="py-2.5 px-3 font-semibold">Reference Interval</th>
                <th className="py-2.5 px-3 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {loading ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">Loading assay catalogue...</td>
                </tr>
              ) : tests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-slate-400">No laboratory tests found.</td>
                </tr>
              ) : (
                tests.map((t) => {
                  const range = t.reference_ranges[0];
                  return (
                    <tr key={t.id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="py-2.5 px-3 font-mono font-bold text-teal-600 dark:text-teal-400">{t.test_code}</td>
                      <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-100">{t.name}</td>
                      <td className="py-2.5 px-3">{t.category_name || '-'}</td>
                      <td className="py-2.5 px-3 font-mono">{t.measurement_unit || '-'}</td>
                      <td className="py-2.5 px-3">
                        {range ? (
                          <div>
                            <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">
                              {range.lower_limit !== null ? range.lower_limit : '0'} &ndash;{' '}
                              {range.upper_limit !== null ? range.upper_limit : '∞'} {range.unit || t.measurement_unit}
                            </span>
                            <span className="block text-[10px] text-slate-400 italic mt-0.5 truncate max-w-xs">
                              Src: {range.source}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">None configured</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedTestForRange(t)}
                          className="gap-1"
                        >
                          <Plus className="w-3.5 h-3.5" /> Interval
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Define Test Modal */}
      <Modal isOpen={isTestModalOpen} onClose={() => setIsTestModalOpen(false)} title="Define Laboratory Test">
        <form onSubmit={handleCreateTest} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Test Code (e.g. HB, GLU)"
              required
              value={testCode}
              onChange={(e) => setTestCode(e.target.value)}
              placeholder="e.g. TSH"
            />
            <Input
              label="Full Test Name"
              required
              value={testName}
              onChange={(e) => setTestName(e.target.value)}
              placeholder="e.g. Thyroid Stimulating Hormone"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                Category
              </label>
              <select
                value={testCatId}
                onChange={(e) => setTestCatId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 dark:border-slate-700 px-3 py-2 text-xs bg-white dark:bg-slate-900 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
            <Input
              label="Measurement Unit"
              value={testUnit}
              onChange={(e) => setTestUnit(e.target.value)}
              placeholder="e.g. uIU/mL"
            />
          </div>

          <Input
            label="Clinical Description"
            value={testDesc}
            onChange={(e) => setTestDesc(e.target.value)}
            placeholder="Clinical utility and analyte physiological context..."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setIsTestModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submittingTest}>
              Save Definition
            </Button>
          </div>
        </form>
      </Modal>

      {/* Add Reference Range Modal */}
      <Modal
        isOpen={Boolean(selectedTestForRange)}
        onClose={() => setSelectedTestForRange(null)}
        title={`Configure Reference Interval — ${selectedTestForRange?.name} (${selectedTestForRange?.test_code})`}
      >
        <form onSubmit={handleCreateRange} className="space-y-4 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label={`Lower Normal Limit (${selectedTestForRange?.measurement_unit || ''})`}
              type="number"
              step="any"
              value={lowerLimit}
              onChange={(e) => setLowerLimit(e.target.value)}
              placeholder="0.0"
            />
            <Input
              label={`Upper Normal Limit (${selectedTestForRange?.measurement_unit || ''})`}
              type="number"
              step="any"
              value={upperLimit}
              onChange={(e) => setUpperLimit(e.target.value)}
              placeholder="100.0"
            />
          </div>

          <Input
            label="Mandatory Clinical Source / Accredited Guideline"
            required
            value={rangeSource}
            onChange={(e) => setRangeSource(e.target.value)}
            placeholder="e.g. CLSI C28-A3, Manufacturer Package Insert Lot #412..."
            helperText="Reference intervals must NOT be invented; record documented provenance."
          />

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" size="sm" onClick={() => setSelectedTestForRange(null)}>
              Cancel
            </Button>
            <Button type="submit" size="sm" isLoading={submittingRange}>
              Add Reference Interval
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
