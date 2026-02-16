import TradeHistory from '../../components/transactions/TradeHistory';
import LeagueSuperlatives from '../../components/transactions/LeagueSuperlatives';

const Archive = () => {
    return (
        <div className="archive-page" style={{ padding: '20px 20px 100px 20px' }}>
            <TradeHistory />
            <LeagueSuperlatives />
        </div>
    );
};

export default Archive;
