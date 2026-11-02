import copy,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from formosync.benchmark import mcq_prompt
from formosync.compare import main as compare
from formosync.scoring.seed_scoring import SCHEMA
from jsonschema import Draft202012Validator

class BenchmarkContracts(unittest.TestCase):
    def test_prompt_is_independent_of_gold_answer(self):
        row={'question':'同一題','choices':dict(zip('ABCD',['甲','乙','丙','丁'])),'answer':'A'}
        changed=copy.deepcopy(row);changed['answer']='D'
        self.assertEqual(mcq_prompt(row),mcq_prompt(changed))

    def test_packaged_semantic_schema_is_valid(self):
        Draft202012Validator.check_schema(SCHEMA)

    def test_comparison_refuses_different_precision(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);identity={k:'same' for k in ['base_model','base_revision','base_manifest_sha256','data_sha256','fixture_sha256','seed','versions','protocol','quantization','runner_sha256']}
            for label in ['base','formosync']:
                p=root/label;p.mkdir();(p/'COMPLETE').write_text('done')
                item=copy.deepcopy(identity)
                if label=='formosync':item['quantization']='different'
                (p/'summary.json').write_text(json.dumps({'identity':item}))
            output=root/'comparison.json'
            with patch('sys.argv',['compare','--base',str(root/'base'),'--formosync',str(root/'formosync'),'--output',str(output)]):
                with self.assertRaisesRegex(ValueError,'quantization'):compare()
            self.assertFalse(output.exists())

if __name__=='__main__':unittest.main()
