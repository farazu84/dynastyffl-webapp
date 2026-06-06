import NextMatchup from './NextMatchup';
import Schedule from './Schedule';

const CurrentMatchups = ({ matchups }) => {
    const nextMatchup = matchups.length > 0 ? matchups[0] : null;
    const remaining = matchups.length > 1 ? matchups.slice(1) : [];

    return (
        <>
            <NextMatchup matchup={nextMatchup} />
            <Schedule matchups={remaining} />
        </>
    );
};

export default CurrentMatchups;
