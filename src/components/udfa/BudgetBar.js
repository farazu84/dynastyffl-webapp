const BudgetBar = ({ budget }) => {
    const { starting_balance, committed, available, waiver_order } = budget;
    const pct = starting_balance > 0 ? Math.round((committed / starting_balance) * 100) : 0;

    return (
        <div className="budget-bar">
            <div className="budget-stats">
                <div className="budget-stat">
                    <span className="budget-label starting">STARTING BALANCE</span>
                    <span className="budget-value">${starting_balance}</span>
                </div>
                <div className="budget-stat">
                    <span className="budget-label committed">COMMITTED</span>
                    <span className="budget-value committed">${committed}</span>
                </div>
                <div className="budget-stat">
                    <span className="budget-label available">AVAILABLE</span>
                    <span className="budget-value">${available}</span>
                </div>
                {waiver_order != null && (
                    <div className="budget-stat">
                        <span className="budget-label waiver">WAIVER NO.</span>
                        <span className="budget-value">{waiver_order}</span>
                    </div>
                )}
            </div>
            <div className="budget-progress-section">
                <div className="budget-progress-track">
                    <div className="budget-progress-fill" style={{ width: `${pct}%` }} />
                </div>
                <span className="budget-progress-label">{pct}% of budget allocated</span>
            </div>
        </div>
    );
};

export default BudgetBar;
