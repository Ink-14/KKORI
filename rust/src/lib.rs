mod raw_searcher;

use pyo3::prelude::*;
use raw_searcher::RustRawStringSearcher;

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustRawStringSearcher>()?;
    Ok(())
}