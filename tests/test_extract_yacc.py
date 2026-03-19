from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.extract_yacc import extract_rules


def test_extract_yacc_handles_ncgen_style_actions_and_literals() -> None:
    yacc_text = r'''
%start ncdesc
%%
ncdesc: NETCDF datasetid rootgroup {if (error_count > 0) YYABORT;} ;

rootgroup: '{'
           groupbody
           subgrouplist
           '}'
         ;

dimdecl:
      dimd '=' constint
          {
            $1->dim.declsize = (size_t)extractint($3);
          }
    | dimd '=' NC_UNLIMITED_K
          {
            $1->dim.isunlimited = 1;
          }
    ;

attrdecllist: /*empty*/ {} | attrdecl ';' attrdecllist {} ;
%%
'''
    rules = extract_rules(yacc_text)["rules"]

    assert "ncdesc" in rules
    assert rules["rootgroup"] == ["'{'\n           groupbody\n           subgrouplist\n           '}'"]
    assert rules["dimdecl"] == ["dimd '=' constint", "dimd '=' NC_UNLIMITED_K"]
    assert rules["attrdecllist"] == ["/*empty*/", "attrdecl ';' attrdecllist"]
