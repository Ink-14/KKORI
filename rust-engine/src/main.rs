mod engine_interface;
use engine_interface::{EnrichedToken, Condition};

fn main() {
    let t = EnrichedToken::new(1, 1, 1, 1, 16, 2, 1);
    let cond = Condition::Tag(1);
    println!("{:#?}", t);
    println!("{:#?}", cond);
}