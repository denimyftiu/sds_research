import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
from shared import lab


class StudyChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def test_inventory_collapses_wrapped_sql_and_keeps_orm(self):
        target=self.root/'repo'; target.mkdir()
        (target/'x.py').write_text('from sqlalchemy import text\nsession.execute(text("SELECT 1"))\nUser.objects.filter(id=1)\n')
        out=self.root/'access.csv'; lab.inventory(target,out)
        rows=lab.read_csv(out)
        self.assertEqual([r['candidate_style'] for r in rows],['raw','orm'])
        self.assertTrue(all(r['review_status']=='pending' for r in rows))

    def test_parse_failure_visible(self):
        target=self.root/'repo'; target.mkdir(); (target/'broken.py').write_text('x = (')
        out=self.root/'access.csv'; lab.inventory(target,out)
        self.assertEqual(len(json.loads(Path(str(out)+'.coverage.json').read_text())['parse_failures']),1)

    def test_failed_scan_cannot_be_scored(self):
        lab.dump(self.root/'run.json',{'runs':{'semgrep':{'valid':False}}})
        with self.assertRaises(ValueError): lab.load_findings(self.root)

    def scans(self):
        target=self.root/'target'; target.mkdir()
        lab.dump(self.root/'scans/run.json',{'target':str(target),'profile':'fixture','runs':{'semgrep':{'valid':True},'bandit':{'valid':True}}})
        lab.dump(self.root/'scans/semgrep.json',{'results':[{'path':str(target/'unsafe.js'),'start':{'line':2},'end':{'line':2},'check_id':'sql','extra':{'severity':'WARNING'}}]})
        lab.dump(self.root/'scans/bandit.json',{'results':[]})
        return target

    def test_unsupported_language_excluded_from_metrics(self):
        self.scans()
        lab.dump(self.root/'labels.json',[{'id':'js','path':'unsafe.js','language':'javascript','vulnerable':True,'start_line':1,'end_line':3},{'id':'py','path':'safe.py','language':'python','vulnerable':False,'start_line':1,'end_line':3}])
        lab.score(self.root/'labels.json', self.root/'scans', self.root/'scores.json')
        metrics=json.loads((self.root/'scores.json').read_text())['metrics']
        self.assertEqual(metrics['semgrep']['tp'],1)
        self.assertEqual(metrics['bandit']['case_count'],1)
        self.assertEqual(metrics['bandit']['fn'],0)
        self.assertIsNone(metrics['bandit']['recall'])

    def test_ambiguous_finding_retained_unmapped(self):
        target=self.scans()
        points=[dict(zip(lab.AP_FIELDS,[str(i),'p','unsafe.js','javascript',2,2,'db.query','raw','','pending'])) for i in range(2)]
        lab.write_csv(self.root/'ap.csv',points,lab.AP_FIELDS)
        lab.normalize(target,self.root/'scans',self.root/'ap.csv',self.root/'f.csv')
        f=lab.read_csv(self.root/'f.csv')[0]
        self.assertEqual(f['match_status'],'ambiguous'); self.assertEqual(f['access_id'],'')

    def test_sample_reproducible_and_protects_reviews(self):
        rows=[dict(zip(lab.F_FIELDS,[str(i),'semgrep','test','p','x.py',1,1,'sql','WARNING',str(i),'raw','matched'])) for i in range(80)]
        lab.write_csv(self.root/'f.csv',rows,lab.F_FIELDS)
        lab.sample(self.root/'f.csv',self.root/'r1.csv'); lab.sample(self.root/'f.csv',self.root/'r2.csv')
        self.assertEqual((self.root/'r1.csv').read_bytes(),(self.root/'r2.csv').read_bytes())
        self.assertEqual(len(lab.read_csv(self.root/'r1.csv')),34)
        with self.assertRaises(ValueError): lab.sample(self.root/'f.csv',self.root/'r1.csv')

    def test_inventory_does_not_overwrite_audit(self):
        target=self.root/'repo'; target.mkdir()
        out=self.root/'access.csv'; out.write_text('human audit')
        with self.assertRaises(ValueError): lab.inventory(target,out)
        self.assertEqual(out.read_text(),'human audit')

    def test_zero_findings_and_unsupported_tool_in_density(self):
        points=[dict(zip(lab.AP_FIELDS,['1','jsrepo','jsrepo/x.js','javascript',1,1,'db.query','raw','','pending']))]
        lab.write_csv(self.root/'ap.csv',points,lab.AP_FIELDS)
        lab.write_csv(self.root/'f.csv',[],lab.F_FIELDS)
        lab.report(self.root/'ap.csv',self.root/'f.csv',self.root/'report.json')
        group=json.loads((self.root/'report.json').read_text())['groups'][0]
        self.assertEqual(group['findings'],{'semgrep':0,'opengrep':0})
        self.assertEqual(group['candidate_findings_per_100_points']['semgrep'],0)

    def test_benchmark_labels_cover_all_files(self):
        labels=json.loads((lab.ROOT/'topic_a/labels.json').read_text())
        sources=lab.source_files(lab.ROOT/'topic_a/benchmark')
        self.assertEqual({c['path'] for c in labels},{p.relative_to(lab.ROOT/'topic_a/benchmark').as_posix() for p in sources})
        self.assertEqual(sum(c['vulnerable'] for c in labels),len(labels)//2)
        for source in sources:
            if source.suffix=='.py': lab.ast.parse(source.read_text())

    def test_scan_cli_and_failure_diagnostics(self):
        target=self.root/'repo'; target.mkdir()
        output=self.root/'scans'
        def fake_run(command, **kwargs):
            if command[1]=='--version':
                return subprocess.CompletedProcess(command,0,'fixture-version','')
            if command[0]=='opengrep':
                self.assertNotIn('--metrics=off',command)
                return subprocess.CompletedProcess(command,2,'','opengrep: example CLI failure')
            return subprocess.CompletedProcess(command,0,'{"results": [], "errors": []}','')
        with patch('shared.lab.subprocess.run',side_effect=fake_run), patch('sys.stderr'):
            with self.assertRaises(SystemExit): lab.scan(target,output)
        failed=json.loads((output/'run.json').read_text())['runs']['opengrep']
        self.assertFalse(failed['valid'])
        self.assertEqual(failed['returncode'],2)
        self.assertEqual(failed['stderr'],'opengrep: example CLI failure')
        self.assertEqual(failed['version'],'fixture-version')
        self.assertEqual(failed['command'][0],'opengrep')

    def test_pilot_preserves_old_runs_and_reviews(self):
        target=self.root/'repo'; target.mkdir(); output=self.root/'b'
        def fake_scan(target, output):
            lab.dump(Path(output)/'run.json',{'target':str(Path(target).resolve()),'profile':'fixture','runs':{'semgrep':{'valid':True}}})
            lab.dump(Path(output)/'semgrep.json',{'results':[]})
        with patch('shared.lab.scan',side_effect=fake_scan), patch('sys.stdout'):
            lab.pilot(target,output)
            first=json.loads((output/'latest.json').read_text())['directory']
            review=output/first/'review.csv'; review.write_text('human review')
            lab.pilot(target,output)
        second=json.loads((output/'latest.json').read_text())['directory']
        self.assertNotEqual(first,second)
        self.assertEqual(review.read_text(),'human review')
        with patch('shared.lab.scan',side_effect=SystemExit('scan failed')), patch('sys.stdout'):
            with self.assertRaises(SystemExit): lab.pilot(target,output)
        self.assertEqual(json.loads((output/'latest.json').read_text())['directory'],second)
        lab.pilot_gates(output,self.root/'policies.json')
        self.assertEqual(json.loads((self.root/'policies.json').read_text())['finding_count'],0)

    def test_pilot_relative_root_with_absolute_temp_directory(self):
        target=self.root/'repo'; target.mkdir()
        output=Path(os.path.relpath(self.root/'b', Path.cwd()))
        original_mkdtemp=lab.tempfile.mkdtemp
        def absolute_mkdtemp(*args, **kwargs):
            # Python 3.12 returns absolute paths even when dir is relative.
            return str(Path(original_mkdtemp(*args, **kwargs)).resolve())
        def fake_scan(target, output):
            lab.dump(Path(output)/'run.json',{'target':str(Path(target).resolve()),'profile':'fixture','runs':{'semgrep':{'valid':True}}})
            lab.dump(Path(output)/'semgrep.json',{'results':[]})
        with patch('shared.lab.tempfile.mkdtemp',side_effect=absolute_mkdtemp), patch('shared.lab.scan',side_effect=fake_scan), patch('sys.stdout'):
            lab.pilot(target, output)
        latest=json.loads((output/'latest.json').read_text())
        self.assertFalse(Path(latest['directory']).is_absolute())
        self.assertTrue((output/latest['directory']/'report.json').is_file())
        lab.pilot_gates(output, self.root/'policies.json')
        self.assertEqual(json.loads((self.root/'policies.json').read_text())['finding_count'],0)

    def test_density_counts_each_tools_findings_separately(self):
        points=[dict(zip(lab.AP_FIELDS,['1','p','p/x.py','python',1,1,'cursor.execute','raw','','pending']))]
        findings=[dict(zip(lab.F_FIELDS,[str(i),tool,'pilot','p','p/x.py',1,1,'sql','WARNING','1','raw','matched'])) for i,tool in enumerate(['semgrep','opengrep','bandit'])]
        lab.write_csv(self.root/'ap.csv',points,lab.AP_FIELDS)
        lab.write_csv(self.root/'f.csv',findings,lab.F_FIELDS)
        lab.report(self.root/'ap.csv',self.root/'f.csv',self.root/'report.json')
        group=json.loads((self.root/'report.json').read_text())['groups'][0]
        self.assertEqual(group['findings'],{'semgrep':1,'opengrep':1,'bandit':1})
        self.assertEqual(group['candidate_findings_per_100_points'],{'semgrep':100,'opengrep':100,'bandit':100})

    def test_empty_project_lock_rejected(self):
        lab.dump(self.root/'lock.json',[])
        with self.assertRaises(ValueError):lab.fetch(self.root/'lock.json',self.root/'sources')

if __name__=='__main__': unittest.main()
