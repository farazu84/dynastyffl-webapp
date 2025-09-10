"""
NFL Statistics Service using FantasyPros scraping with caching
Replaces OpenRouter approach with direct FantasyPros scraping for reliable data.
"""
import os
import json
from datetime import datetime
from app.league_state_manager import get_current_year, get_current_week
from app.logic.player_stats import get_player_stats, get_position_stats

class NFLStatsService:
    """
    Service for fetching NFL statistics from FantasyPros using direct scraping.
    """
    
    @staticmethod
    def enhance_players_with_stats(players_list, year=None, week=None):
        """
        Enhance player objects with their NFL statistics from FantasyPros.
        
        Args:
            players_list: List of player objects with first_name and last_name attributes
            year: NFL season year
            week: NFL week number (None for season stats)
            
        Returns:
            List of enhanced player dictionaries with stats included
        """
        try:
            # Extract player names and create mapping
            player_names = []
            player_mapping = {}
            
            for player in players_list:
                if hasattr(player, 'first_name') and hasattr(player, 'last_name'):
                    full_name = f"{player.first_name} {player.last_name}"
                    player_names.append(full_name)
                    player_mapping[full_name] = player
            
            if not player_names:
                print("No valid player names provided")
                return [player.serialize() for player in players_list]
            
            print(f"Enhancing {len(player_names)} players with FantasyPros stats: {', '.join(player_names[:5])}{'...' if len(player_names) > 5 else ''}")
            
            # Get stats from FantasyPros scraper
            stats_data = get_player_stats(player_names, year, week)
            matched_players = stats_data.get('matched_players', {})
            
            # Enhance each player object
            enhanced_players = []
            for player in players_list:
                # Start with serialized player data
                enhanced_player = player.serialize()
                
                # Try to find matching stats
                full_name = f"{player.first_name} {player.last_name}"
                player_stats = matched_players.get(full_name)
                
                if player_stats:
                    # Add all stats to the player object
                    enhanced_player.update(player_stats)
                    enhanced_player['has_nfl_stats'] = True
                    print(f"  ✅ Enhanced {full_name} with NFL stats")
                else:
                    enhanced_player['has_nfl_stats'] = False
                    print(f"  ❌ No stats found for {full_name}")
                
                enhanced_players.append(enhanced_player)
            
            return enhanced_players
            
        except Exception as e:
            print(f"Error enhancing players with stats: {e}")
            # Return original serialized players if enhancement fails
            return [player.serialize() for player in players_list]
    
    @staticmethod
    def format_fantasypros_stats_for_report(stats_data):
        """
        Format FantasyPros statistics data for inclusion in pregame reports.
        
        Args:
            stats_data: Dictionary containing player statistics from FantasyPros
            
        Returns:
            Formatted string ready for inclusion in AI prompts
        """
        try:
            if 'error' in stats_data:
                return f"FantasyPros statistics not available: {stats_data['error']}"
            
            players = stats_data.get('players', {})
            if not players:
                return "No player statistics found on FantasyPros"
            
            formatted_output = []
            formatted_output.append(f"=== FANTASYPROS STATISTICS ({stats_data.get('source', 'FantasyPros')}) ===")
            formatted_output.append(f"Players Found: {stats_data.get('total_found', 0)}/{stats_data.get('total_requested', 0)}")
            
            if stats_data.get('week'):
                formatted_output.append(f"Week: {stats_data.get('week')} of {stats_data.get('year')}")
            else:
                formatted_output.append(f"Season: {stats_data.get('year')} Totals")
            
            formatted_output.append("")
            
            for player_name, player_info in players.items():
                stats = player_info.get('stats', {})
                formatted_output.append(f"**{player_info.get('name', player_name).title()}** ({player_info.get('team', 'N/A')}) - {player_info.get('position', 'N/A')}")
                
                # Format key statistics
                stat_lines = []
                
                # Fantasy points (always show if available)
                #if player_info.get('fantasy_points'):
                #    stat_lines.append(f"FPTS: {player_info.get('fantasy_points')}")
                #if player_info.get('fantasy_points_per_game'):
                #    stat_lines.append(f"FPTS/G: {player_info.get('fantasy_points_per_game')}")
                
                # Position-specific stats
                position = player_info.get('position', '').upper()
                
                if position == 'QB':
                    if stats.get('completions') and stats.get('attempts'):
                        stat_lines.append(f"Passing: {stats.get('completions')}/{stats.get('attempts')} ({stats.get('completion_percentage', 0)}%)")
                    if stats.get('passing_yards'):
                        stat_lines.append(f"Pass Yds: {stats.get('passing_yards')}")
                    if stats.get('passing_tds'):
                        stat_lines.append(f"Pass TDs: {stats.get('passing_tds')}")
                    if stats.get('interceptions'):
                        stat_lines.append(f"INTs: {stats.get('interceptions')}")
                    if stats.get('rushing_yards'):
                        stat_lines.append(f"Rush Yds: {stats.get('rushing_yards')}")
                    if stats.get('rushing_tds'):
                        stat_lines.append(f"Rush TDs: {stats.get('rushing_tds')}")
                
                elif position == 'RB':
                    if stats.get('rushing_attempts'):
                        stat_lines.append(f"Rush Att: {stats.get('rushing_attempts')}")
                    if stats.get('rushing_yards'):
                        stat_lines.append(f"Rush Yds: {stats.get('rushing_yards')}")
                    if stats.get('rushing_tds'):
                        stat_lines.append(f"Rush TDs: {stats.get('rushing_tds')}")
                    if stats.get('receptions'):
                        stat_lines.append(f"Rec: {stats.get('receptions')}")
                    if stats.get('receiving_yards'):
                        stat_lines.append(f"Rec Yds: {stats.get('receiving_yards')}")
                    if stats.get('receiving_tds'):
                        stat_lines.append(f"Rec TDs: {stats.get('receiving_tds')}")
                
                elif position in ['WR', 'TE']:
                    if stats.get('receptions'):
                        stat_lines.append(f"Rec: {stats.get('receptions')}")
                    if stats.get('targets'):
                        stat_lines.append(f"Tgt: {stats.get('targets')}")
                    if stats.get('receiving_yards'):
                        stat_lines.append(f"Rec Yds: {stats.get('receiving_yards')}")
                    if stats.get('receiving_tds'):
                        stat_lines.append(f"Rec TDs: {stats.get('receiving_tds')}")
                    if stats.get('rushing_yards'):
                        stat_lines.append(f"Rush Yds: {stats.get('rushing_yards')}")
                
                # Games played and roster %
                if stats.get('games_played'):
                    stat_lines.append(f"G: {stats.get('games_played')}")
                if player_info.get('roster_percentage'):
                    stat_lines.append(f"Rostered: {player_info.get('roster_percentage')}")
                
                if stat_lines:
                    formatted_output.append("  " + " | ".join(stat_lines))
                else:
                    formatted_output.append("  No detailed statistics available")
                
                formatted_output.append("")
            
            formatted_output.append(f"Data scraped at: {stats_data.get('scraped_at', 'N/A')}")
            formatted_output.append("Source: FantasyPros.com (Direct Scraping)")
            
            return "\n".join(formatted_output)
            
        except Exception as e:
            return f"Error formatting FantasyPros statistics: {str(e)}"

    @staticmethod
    def format_enhanced_players_for_report(enhanced_players):
        """
        Format enhanced player data for inclusion in pregame/postgame reports.
        
        Args:
            enhanced_players: List of enhanced player dictionaries with stats
            
        Returns:
            Formatted string ready for inclusion in AI prompts
        """
        if not enhanced_players:
            return "No player data available."
        
        output = []
        output.append("=== NFL STATISTICS (FantasyPros) ===")
        
        # Count players with stats
        players_with_stats = [p for p in enhanced_players if p.get('has_nfl_stats', False)]
        output.append(f"Players Found: {len(players_with_stats)}/{len(enhanced_players)}")
        output.append("")
        
        for player_data in enhanced_players:
            name = f"{player_data.get('first_name', '')} {player_data.get('last_name', '')}".strip()
            position = player_data.get('position', 'N/A')
            
            if not player_data.get('has_nfl_stats', False):
                output.append(f"**{name}** ({position}) - No NFL stats available")
                output.append("")
                continue
            
            team = player_data.get('team', 'N/A')
            output.append(f"**{name}** ({team}, {position})")
            
            # Fantasy stats
            #fpts = player_data.get('fantasy_points', 0)
            #fpts_per_game = player_data.get('fantasy_points_per_game', 0)
            #games = player_data.get('games_played', 0)
            #roster_pct = player_data.get('roster_percentage', '0%')
            
            #output.append(f"  FPTS: {fpts} | FPTS/G: {fpts_per_game} | Games: {games} | ROST: {roster_pct}")
            
            # Position-specific stats
            stats_lines = []
            
            if position == 'QB':
                comp = player_data.get('completions', 0)
                att = player_data.get('attempts', 0)
                pct = player_data.get('completion_percentage', 0)
                pass_yds = player_data.get('passing_yards', 0)
                pass_tds = player_data.get('passing_tds', 0)
                ints = player_data.get('interceptions', 0)
                rush_att = player_data.get('rushing_attempts', 0)
                rush_yds = player_data.get('rushing_yards', 0)
                rush_tds = player_data.get('rushing_tds', 0)
                
                if comp > 0 or pass_yds > 0:
                    stats_lines.append(f"Passing: {comp}/{att} ({pct}%) for {pass_yds} yds, {pass_tds} TDs, {ints} INTs")
                if rush_att > 0 or rush_yds > 0:
                    stats_lines.append(f"Rushing: {rush_att} att, {rush_yds} yds, {rush_tds} TDs")
                    
            elif position in ['RB', 'WR', 'TE']:
                rec = player_data.get('receptions', 0)
                tgt = player_data.get('targets', 0)
                rec_yds = player_data.get('receiving_yards', 0)
                rec_tds = player_data.get('receiving_tds', 0)
                
                if position == 'RB':
                    rush_att = player_data.get('rushing_attempts', 0)
                    rush_yds = player_data.get('rushing_yards', 0)
                    rush_tds = player_data.get('rushing_tds', 0)
                    if rush_att > 0 or rush_yds > 0:
                        stats_lines.append(f"Rushing: {rush_att} att, {rush_yds} yds, {rush_tds} TDs")
                
                if rec > 0 or rec_yds > 0:
                    stats_lines.append(f"Receiving: {rec} rec, {tgt} tgt, {rec_yds} yds, {rec_tds} TDs")
                    
            elif position == 'K':
                fgm = player_data.get('field_goals_made', 0)
                fga = player_data.get('field_goals_attempted', 0)
                fg_pct = player_data.get('field_goal_percentage', 0)
                xpm = player_data.get('extra_points_made', 0)
                xpa = player_data.get('extra_points_attempted', 0)
                
                stats_lines.append(f"FG: {fgm}/{fga} ({fg_pct}%), XP: {xpm}/{xpa}")
            
            if stats_lines:
                for line in stats_lines:
                    output.append(f"  {line}")
            else:
                output.append("  No detailed statistics available")
            
            output.append("")
        
        return "\n".join(output)


def get_enhanced_player_data(players):
    """
    Get enhanced player data with previous week or season statistics from FantasyPros.
    
    Args:
        players: List of player objects
        
    Returns:
        Dictionary containing player data with previous week or season statistics
    """
    current_week = get_current_week()
    current_year = get_current_year()
    
    if not current_week or not current_year:
        return {"error": "Unable to determine current week/year"}
    
    # Determine what type of data we're getting
    is_week_1 = current_week is None or current_week <= 1
    data_type = "season_totals" if is_week_1 else "weekly_stats"
    
    print(f"Data type: {data_type} (Week {current_week} of {current_year})")
    
    # Get enhanced players with stats from FantasyPros
    if is_week_1:
        # Get previous season totals
        previous_year = current_year - 1 if current_year else 2024
        print(f"Fetching previous season ({previous_year}) stats from FantasyPros...")
        enhanced_players = NFLStatsService.enhance_players_with_stats(players, year=previous_year, week=None)
    else:
        # Get previous week stats
        previous_week = current_week - 1
        print(f"Fetching Week {previous_week} stats from FantasyPros...")
        enhanced_players = NFLStatsService.enhance_players_with_stats(players, year=current_year, week=previous_week)
    
    # Format the enhanced players for the report
    formatted_stats = NFLStatsService.format_enhanced_players_for_report(enhanced_players)
    
    return {
        "current_week": current_week,
        "previous_week": current_week - 1 if current_week and current_week > 1 else None,
        "previous_season": current_year - 1 if is_week_1 else None,
        "year": current_year,
        "data_type": data_type,
        "enhanced_players": enhanced_players,
        "formatted_stats": formatted_stats,
        "source": "FantasyPros Scraper"
    }
