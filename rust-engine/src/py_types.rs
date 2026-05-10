use pyo3::prelude::*;

#[pyclass]
pub struct TagCondition {
    pub tag: String,
}

#[pymethods]
impl TagCondition {
    #[new]
    pub fn new(tag: String) -> Self {
        TagCondition { tag }
    }
}

#[pyclass]
pub struct FormCondition {
    pub form: String,
}

#[pymethods]
impl FormCondition {
    #[new]
    pub fn new(form: String) -> Self {
        FormCondition { form }
    }
}

#[pyclass]
pub struct TagAndFormCondition {
    pub form: String,
    pub tag: String,
}

#[pymethods]
impl TagAndFormCondition {
    #[new]
    pub fn new(form: String, tag: String) -> Self {
        TagAndFormCondition { form, tag }
    }
}

#[pyclass]
pub struct LemmaCondition {
    pub lemma: String,
}

#[pymethods]
impl LemmaCondition {
    #[new]
    pub fn new(lemma: String) -> Self {
        LemmaCondition { lemma }
    }
}

#[pyclass]
pub struct AnyCondition;

#[pymethods]
impl AnyCondition {
    #[new]
    pub fn new() -> Self { AnyCondition }
}

#[pyclass]
pub struct AnyBatchimCondition;

#[pymethods]
impl AnyBatchimCondition {
    #[new]
    pub fn new() -> Self { AnyBatchimCondition }
}

#[pyclass]
pub struct NoBatchimCondition;

#[pymethods]
impl NoBatchimCondition {
    #[new]
    pub fn new() -> Self { NoBatchimCondition }
}

#[pyclass]
pub struct BatchimCondition {
    pub batchim: String,
}

#[pymethods]
impl BatchimCondition {
    #[new]
    pub fn new(batchim: String) -> Self {
        BatchimCondition { batchim }
    }
}

#[pyclass]
pub struct LengthCondition {
    pub length: u8,
}

#[pymethods]
impl LengthCondition {
    #[new]
    pub fn new(length: u8) -> Self {
        LengthCondition { length }
    }
}

#[pyclass]
pub struct FirstTokenCondition;

#[pymethods]
impl FirstTokenCondition {
    #[new]
    pub fn new() -> Self { FirstTokenCondition }
}

#[pyclass]
pub struct TagSetCondition {
    pub tags: Vec<String>,
}

#[pymethods]
impl TagSetCondition {
    #[new]
    pub fn new(tags: Vec<String>) -> Self {
        TagSetCondition { tags }
    }
}

#[pyclass]
pub struct FormSetCondition {
    pub forms: Vec<String>,
}

#[pymethods]
impl FormSetCondition {
    #[new]
    pub fn new(forms: Vec<String>) -> Self {
        FormSetCondition { forms }
    }
}

#[pyclass]
pub struct AndCondition {
    pub conditions: Vec<PyObject>,
}

#[pymethods]
impl AndCondition {
    #[new]
    pub fn new(conditions: Vec<PyObject>) -> Self {
        AndCondition { conditions }
    }
}

#[pyclass]
pub struct OrCondition {
    pub conditions: Vec<PyObject>,
}

#[pymethods]
impl OrCondition {
    #[new]
    pub fn new(conditions: Vec<PyObject>) -> Self {
        OrCondition { conditions }
    }
}

#[pyclass]
pub struct NotCondition {
    pub condition: PyObject,
}

#[pymethods]
impl NotCondition {
    #[new]
    pub fn new(condition: PyObject) -> Self {
        NotCondition { condition }
    }
}