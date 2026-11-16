"""Regression checks for all-folder coverage and invalid C4 inputs."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import validate_lab5 as v

class ValidationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        patcher = patch.object(v, 'ROOT', self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.write('vendor/C4_Container.puml', 'upstream')

    def write(self, name, text):
        p = self.root/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf8')
        return p

    def diagram(self, extra='Rel(a,b,"call","HTTPS")'):
        return ('@startuml\n!pragma layout smetana\n!include ../vendor/C4_Container.puml\n'
                'Container(a,"A","Python","A")\nContainer(b,"B","Python","B")\n'
                + extra + '\n@enduml')

    def test_discovers_frontend_and_future_folders(self):
        for path in ['diagrams/a.puml','lab5/b.puml','front_diagramms/c.puml','new_member/d.puml']:
            self.write(path,'@startuml\n@enduml')
        self.write('.git/hidden.puml','ignore')
        self.assertEqual(len(v.discover(self.root)),4)

    def test_valid_diagram(self):
        v.lint(self.write('front_diagramms/good.puml',self.diagram()))

    def test_bad_relationships_and_styles(self):
        for extra in ['Rel_D(a,b,"call","HTTPS")','skinparam dpi 220','Rel(a,missing,"call","HTTPS")']:
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                v.lint(self.write('front_diagramms/bad.puml',self.diagram(extra)))

    def test_missing_and_network_include(self):
        for target in ['missing.puml','https://example.org/C4.puml']:
            with self.subTest(target=target),self.assertRaises((ValueError,FileNotFoundError)):
                v.lint(self.write('front_diagramms/bad.puml','@startuml\n!include '+target+'\n@enduml'))

    def test_transitive_c4_is_linted(self):
        self.write('front_diagramms/fragment.puml','!include ../vendor/C4_Container.puml\nRel_D(a,b,"call","HTTPS")')
        with self.assertRaises(ValueError):
            v.lint(self.write('front_diagramms/main.puml','@startuml\n!pragma layout smetana\n!include fragment.puml\n@enduml'))

    def test_nested_standalone_is_rejected(self):
        self.write('front_diagramms/full.puml',self.diagram())
        with self.assertRaises(ValueError):
            v.lint(self.write('front_diagramms/main.puml','@startuml\n!include full.puml\n@enduml'))

    def test_include_cycle(self):
        self.write('front_diagramms/first.puml','!include second.puml')
        self.write('front_diagramms/second.puml','!include first.puml')
        with self.assertRaises(ValueError):v.expand(self.root/'front_diagramms/first.puml')

if __name__=='__main__':unittest.main()
