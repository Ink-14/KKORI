mod raw_searcher;
mod engine_interface;
mod py_types;
mod rule_checker_engine;

use pyo3::prelude::*;
use raw_searcher::RustRawStringSearcher;
use py_types::*;
use engine_interface::{SpellErrorType, SpellError};
use rule_checker_engine::{RuleCheckerBuilder, RuleChecker};

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustRawStringSearcher>()?;

    m.add_class::<RuleCheckerBuilder>()?;
    m.add_class::<RuleChecker>()?;
    m.add_class::<SpellErrorType>()?;
    m.add_class::<SpellError>()?;

    m.add_class::<TagCondition>()?;
    m.add_class::<FormCondition>()?;
    m.add_class::<TagAndFormCondition>()?;
    m.add_class::<LemmaCondition>()?;
    m.add_class::<AnyCondition>()?;
    m.add_class::<AnyBatchimCondition>()?;
    m.add_class::<NoBatchimCondition>()?;
    m.add_class::<BatchimCondition>()?;
    m.add_class::<LengthCondition>()?;
    m.add_class::<FirstTokenCondition>()?;
    m.add_class::<TagSetCondition>()?;
    m.add_class::<FormSetCondition>()?;
    m.add_class::<AndCondition>()?;
    m.add_class::<OrCondition>()?;
    m.add_class::<NotCondition>()?;

    Ok(())
}
