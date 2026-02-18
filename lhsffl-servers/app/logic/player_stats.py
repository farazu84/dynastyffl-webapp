"""
Player Statistics Logic - FantasyPros Scraping with Caching
Scrapes FantasyPros.com for NFL player statistics with intelligent caching.
"""
import requests
from bs4 import BeautifulSoup
import re
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import time

class FantasyProsScraper:
    """
    Scraper for FantasyPros NFL statistics with caching capabilities.
    """
    
    def __init__(self, cache_dir="fantasypros_cache", cache_duration_hours=24):
        """
        Initialize the scraper with caching configuration.
        
        Args:
            cache_dir: Directory to store cached data (relative to server root)
            cache_duration_hours: How long to cache data (in hours)
        """
        # Store cache in server directory instead of /tmp
        server_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.cache_dir = os.path.join(server_root, cache_dir)
        self.html_cache_dir = os.path.join(self.cache_dir, "html_pages")
        self.data_cache_dir = os.path.join(self.cache_dir, "parsed_data")
        
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.base_url = "https://www.fantasypros.com/nfl/stats"
        
        # Create cache directories if they don't exist
        os.makedirs(self.html_cache_dir, exist_ok=True)
        os.makedirs(self.data_cache_dir, exist_ok=True)
        
        # Headers to avoid being blocked
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _get_cache_key(self, position: str, year: int, week: Optional[int] = None) -> str:
        """Generate a cache key for the request."""
        if week:
            return f"{position}_{year}_week_{week}"
        else:
            return f"{position}_{year}_season"
    
    def _get_cache_path(self, cache_key: str, file_type: str = "json") -> str:
        """Get the full path for a cache file."""
        if file_type == "html":
            return os.path.join(self.html_cache_dir, f"{cache_key}.html")
        else:
            return os.path.join(self.data_cache_dir, f"{cache_key}.json")
    
    def _get_html_cache_path(self, cache_key: str) -> str:
        """Get the full path for an HTML cache file."""
        return self._get_cache_path(cache_key, "html")
    
    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cached data is still valid."""
        if not os.path.exists(cache_path):
            return False
        
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        return datetime.now() - file_time < self.cache_duration
    
    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """Save data to cache."""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': data
                }, f, indent=2)
            print(f"Cached FantasyPros data: {cache_key}")
        except Exception as e:
            print(f"Error saving to cache: {e}")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Load data from cache."""
        cache_path = self._get_cache_path(cache_key)
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                print(f"Using cached FantasyPros data: {cache_key}")
                return cached['data']
        except Exception as e:
            print(f"Error loading from cache: {e}")
            return None
    
    def _save_html_to_cache(self, cache_key: str, html_content: str, url: str) -> None:
        """Save HTML content to cache."""
        html_cache_path = self._get_html_cache_path(cache_key)
        try:
            with open(html_cache_path, 'w', encoding='utf-8') as f:
                # Add metadata at the top of the HTML file
                f.write(f"<!-- Cached from: {url} -->\n")
                f.write(f"<!-- Cached at: {datetime.now().isoformat()} -->\n")
                f.write(f"<!-- Cache key: {cache_key} -->\n\n")
                f.write(html_content)
            print(f"Cached HTML page: {cache_key}")
        except Exception as e:
            print(f"Error saving HTML to cache: {e}")
    
    def _load_html_from_cache(self, cache_key: str) -> Optional[str]:
        """Load HTML content from cache."""
        html_cache_path = self._get_html_cache_path(cache_key)
        if not self._is_cache_valid(html_cache_path):
            return None
        
        try:
            with open(html_cache_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Remove our metadata comments
                lines = content.split('\n')
                # Skip the first few lines if they're our metadata
                start_index = 0
                for i, line in enumerate(lines[:10]):  # Check first 10 lines
                    if line.startswith('<!-- Cached') or line.strip() == '':
                        start_index = i + 1
                    else:
                        break
                
                html_content = '\n'.join(lines[start_index:])
                print(f"Using cached HTML page: {cache_key}")
                return html_content
        except Exception as e:
            print(f"Error loading HTML from cache: {e}")
            return None
    
    def _build_url(self, position: str, year: int, week: Optional[int] = None) -> str:
        """Build the FantasyPros URL for the given parameters."""
        position_map = {
            'QB': 'qb', 'RB': 'rb', 'WR': 'wr', 'TE': 'te', 'K': 'k', 'DST': 'dst'
        }
        
        pos_code = position_map.get(position.upper(), 'qb')
        url = f"{self.base_url}/{pos_code}.php"
        
        params = {
            'year': year,
            'scoring': 'PPR'
        }
        
        if week:
            params['range'] = 'week'
            params['week'] = week
        else:
            params['range'] = 'full'
        
        # Build query string
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{url}?{query_string}"
    
    def _safe_int(self, cell) -> int:
        """Safely convert cell text to integer."""
        try:
            text = cell.get_text(strip=True)
            # Handle negative values and special characters
            text = text.replace('\\-', '-').replace(',', '')
            if text in ['', '-', 'N/A']:
                return 0
            return int(float(text))  # Convert to float first to handle decimals
        except (ValueError, AttributeError):
            return 0
    
    def _safe_float(self, cell) -> float:
        """Safely convert cell text to float."""
        try:
            text = cell.get_text(strip=True)
            # Handle negative values and special characters
            text = text.replace('\\-', '-').replace(',', '')
            if text in ['', '-', 'N/A']:
                return 0.0
            return float(text)
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_player_row(self, row, position: str) -> Optional[Dict]:
        """Parse a single player row from the FantasyPros table."""
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 10:  # Minimum expected columns
                return None
            
            # Extract player name and team from the second column (index 1)
            player_cell = cells[1]
            player_link = player_cell.find('a')
            
            if not player_link:
                return None
            
            player_name = player_link.get_text(strip=True)
            
            # Extract team from parentheses in the cell text
            cell_text = player_cell.get_text(strip=True)
            team_match = re.search(r'\(([^)]+)\)', cell_text)
            team = team_match.group(1) if team_match else 'N/A'
            
            # Initialize player data
            player_data = {
                'name': player_name,
                'team': team,
                'position': position.upper(),
                'rank': cells[0].get_text(strip=True),
            }
            
            # Parse position-specific stats based on table structure
            if position.upper() == 'QB':
                # QB table: CMP, ATT, PCT, YDS, Y/A, TD, INT, SACKS, ATT, YDS, TD, FL, G, FPTS, FPTS/G, ROST
                try:
                    player_data.update({
                        'completions': self._safe_int(cells[2]),
                        'attempts': self._safe_int(cells[3]),
                        'completion_percentage': self._safe_float(cells[4]),
                        'passing_yards': self._safe_int(cells[5]),
                        'yards_per_attempt': self._safe_float(cells[6]),
                        'passing_tds': self._safe_int(cells[7]),
                        'interceptions': self._safe_int(cells[8]),
                        'sacks': self._safe_int(cells[9]),
                        'rushing_attempts': self._safe_int(cells[10]),
                        'rushing_yards': self._safe_int(cells[11]),
                        'rushing_tds': self._safe_int(cells[12]),
                        'fumbles_lost': self._safe_int(cells[13]),
                        'games_played': self._safe_int(cells[14]),
                        'roster_percentage': cells[17].get_text(strip=True) if len(cells) > 17 else '0%'
                    })
                except IndexError:
                    # Handle cases where some columns might be missing
                    pass
            
            elif position.upper() == 'RB':
                # RB table: ATT, YDS, Y/A, LG, 20+, TD, REC, TGT, YDS, Y/R, TD, FL, G, FPTS, FPTS/G, ROST
                try:
                    player_data.update({
                        'rushing_attempts': self._safe_int(cells[2]),
                        'rushing_yards': self._safe_int(cells[3]),
                        'yards_per_attempt': self._safe_float(cells[4]),
                        'longest_rush': self._safe_int(cells[5]),
                        'rushes_20_plus': self._safe_int(cells[6]),
                        'rushing_tds': self._safe_int(cells[7]),
                        'receptions': self._safe_int(cells[8]),
                        'targets': self._safe_int(cells[9]),
                        'receiving_yards': self._safe_int(cells[10]),
                        'yards_per_reception': self._safe_float(cells[11]),
                        'receiving_tds': self._safe_int(cells[12]),
                        'fumbles_lost': self._safe_int(cells[13]),
                        'games_played': self._safe_int(cells[14]),
                        'roster_percentage': cells[17].get_text(strip=True) if len(cells) > 17 else '0%'
                    })
                except IndexError:
                    # Handle cases where some columns might be missing
                    pass
            
            elif position.upper() == 'WR':
                # WR table: REC, TGT, YDS, Y/R, LG, 20+, TD, ATT, YDS, TD, FL, G, FPTS, FPTS/G, ROST
                try:
                    player_data.update({
                        'receptions': self._safe_int(cells[2]),
                        'targets': self._safe_int(cells[3]),
                        'receiving_yards': self._safe_int(cells[4]),
                        'yards_per_reception': self._safe_float(cells[5]),
                        'longest_reception': self._safe_int(cells[6]),
                        'receptions_20_plus': self._safe_int(cells[7]),
                        'receiving_tds': self._safe_int(cells[8]),
                        'rushing_attempts': self._safe_int(cells[9]),
                        'rushing_yards': self._safe_int(cells[10]),
                        'rushing_tds': self._safe_int(cells[11]),
                        'fumbles_lost': self._safe_int(cells[12]),
                        'games_played': self._safe_int(cells[13]),
                        'roster_percentage': cells[16].get_text(strip=True) if len(cells) > 16 else '0%'
                    })
                except IndexError:
                    # Handle cases where some columns might be missing
                    pass
            
            elif position.upper() == 'TE':
                # TE table: REC, TGT, YDS, Y/R, LG, 20+, TD, FL, G, FPTS, FPTS/G, ROST
                try:
                    player_data.update({
                        'receptions': self._safe_int(cells[2]),
                        'targets': self._safe_int(cells[3]),
                        'receiving_yards': self._safe_int(cells[4]),
                        'yards_per_reception': self._safe_float(cells[5]),
                        'longest_reception': self._safe_int(cells[6]),
                        'receptions_20_plus': self._safe_int(cells[7]),
                        'receiving_tds': self._safe_int(cells[8]),
                        'fumbles_lost': self._safe_int(cells[9]),
                        'games_played': self._safe_int(cells[10]),
                        'roster_percentage': cells[13].get_text(strip=True) if len(cells) > 13 else '0%'
                    })
                except IndexError:
                    # Handle cases where some columns might be missing
                    pass
            
            elif position.upper() == 'K':
                # K table: FGM, FGA, PCT, LG, 1-19, 20-29, 30-39, 40-49, 50+, XPM, XPA, G, FPTS, FPTS/G, ROST
                try:
                    player_data.update({
                        'field_goals_made': self._safe_int(cells[2]),
                        'field_goals_attempted': self._safe_int(cells[3]),
                        'field_goal_percentage': self._safe_float(cells[4]),
                        'longest_field_goal': self._safe_int(cells[5]),
                        'fg_1_19': self._safe_int(cells[6]),
                        'fg_20_29': self._safe_int(cells[7]),
                        'fg_30_39': self._safe_int(cells[8]),
                        'fg_40_49': self._safe_int(cells[9]),
                        'fg_50_plus': self._safe_int(cells[10]),
                        'extra_points_made': self._safe_int(cells[11]),
                        'extra_points_attempted': self._safe_int(cells[12]),
                        'games_played': self._safe_int(cells[13]),
                        'roster_percentage': cells[16].get_text(strip=True) if len(cells) > 16 else '0%'
                    })
                except IndexError:
                    # Handle cases where some columns might be missing
                    pass
            
            return player_data
            
        except Exception as e:
            print(f"Error parsing player row: {e}")
            return None
    
    def scrape_position_stats(self, position: str, year: int, week: Optional[int] = None) -> Dict:
        """
        Scrape statistics for a specific position from FantasyPros.
        
        Args:
            position: Player position (QB, RB, WR, TE, K, DST)
            year: NFL season year
            week: NFL week number (None for season stats)
            
        Returns:
            Dictionary containing player statistics
        """
        cache_key = self._get_cache_key(position, year, week)
        
        # Try to load parsed data from cache first
        cached_data = self._load_from_cache(cache_key)
        if cached_data:
            return cached_data
        
        # Build URL
        url = self._build_url(position, year, week)
        
        # Try to load HTML from cache first
        cached_html = self._load_html_from_cache(cache_key)
        
        if cached_html:
            print(f"Using cached HTML for {position} {year} week {week}")
            html_content = cached_html
        else:
            # Make request to FantasyPros
            print(f"Fetching fresh data from FantasyPros: {url}")
            try:
                # Add delay to be respectful to the server
                time.sleep(1)
                
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                html_content = response.text
                
                # Save HTML to cache
                self._save_html_to_cache(cache_key, html_content, url)
                
            except Exception as e:
                print(f"Error fetching from FantasyPros: {e}")
                return {'players': [], 'error': str(e)}
        
        try:
            # Parse HTML (whether from cache or fresh)
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the stats table
            stats_table = soup.find('table')
            if not stats_table:
                print(f"No stats table found for {position}")
                return {'players': [], 'error': 'No table found'}
            
            # Extract player data
            players = []
            tbody = stats_table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # If no tbody, get all rows except the first (header)
                rows = stats_table.find_all('tr')[1:]
            
            for row in rows:
                player_data = self._parse_player_row(row, position)
                if player_data:
                    players.append(player_data)
            
            result = {
                'position': position.upper(),
                'year': year,
                'week': week,
                'players': players,
                'total_players': len(players),
                'scraped_at': datetime.now().isoformat(),
                'source_url': url,
                'cached_html': cached_html is not None
            }
            
            # Save parsed data to cache
            self._save_to_cache(cache_key, result)
            
            source = "cached HTML" if cached_html else "fresh FantasyPros data"
            print(f"Successfully processed {len(players)} {position} players from {source}")
            return result
            
        except Exception as e:
            print(f"Error parsing FantasyPros data for {position}: {e}")
            return {'players': [], 'error': str(e)}
    
    def get_player_stats(self, player_names: List[str], year: int, week: Optional[int] = None) -> Dict:
        """
        Get statistics for specific players across all positions.
        
        Args:
            player_names: List of player names to find
            year: NFL season year
            week: NFL week number (None for season stats)
            
        Returns:
            Dictionary with matched player statistics
        """
        positions = ['QB', 'RB', 'WR', 'TE', 'K']
        all_players = {}
        matched_players = {}
        
        # Scrape all positions
        for position in positions:
            position_data = self.scrape_position_stats(position, year, week)
            for player in position_data.get('players', []):
                player_key = player['name'].lower().strip()
                all_players[player_key] = player
        
        # Match requested players
        for requested_name in player_names:
            requested_key = requested_name.lower().strip()
            
            # Try exact match first
            if requested_key in all_players:
                matched_players[requested_name] = all_players[requested_key]
            else:
                # Try partial matching with improved logic for suffixes
                matched = False
                for scraped_key, player_data in all_players.items():
                    # Split names and normalize
                    requested_parts = requested_key.replace('.', '').split()
                    scraped_parts = scraped_key.replace('.', '').split()
                    
                    # Handle common suffixes
                    suffixes = ['ii', 'iii', 'iv', 'jr', 'jr.', 'sr', 'sr.']
                    
                    # Remove suffixes from both for comparison
                    req_clean = [p for p in requested_parts if p not in suffixes]
                    scraped_clean = [p for p in scraped_parts if p not in suffixes]
                    
                    # Check if the core name parts match
                    if len(req_clean) >= 2:  # At least first and last name
                        # Try exact match of clean names
                        if req_clean == scraped_clean[:len(req_clean)]:
                            matched_players[requested_name] = player_data
                            matched = True
                            break
                        
                        # Try partial match - all requested parts in scraped name
                        if all(part in scraped_clean for part in req_clean):
                            matched_players[requested_name] = player_data
                            matched = True
                            break
                        
                        # Try fuzzy match for slight differences
                        if len(req_clean) == 2 and len(scraped_clean) >= 2:
                            # Check first and last name similarity
                            first_match = req_clean[0] in scraped_clean[0] or scraped_clean[0] in req_clean[0]
                            last_match = req_clean[-1] in scraped_clean[-1] or scraped_clean[-1] in req_clean[-1]
                            if first_match and last_match:
                                matched_players[requested_name] = player_data
                                matched = True
                                break
                
                # If still no match, try the original simple method
                if not matched:
                    for scraped_key, player_data in all_players.items():
                        if all(part in scraped_key for part in requested_key.split() if len(part) > 2):
                            matched_players[requested_name] = player_data
                            break
        
        return {
            'matched_players': matched_players,
            'total_found': len(matched_players),
            'total_requested': len(player_names),
            'year': year,
            'week': week,
            'scraped_at': datetime.now().isoformat()
        }
    
    def get_cache_info(self) -> Dict:
        """Get information about cached files."""
        try:
            html_files = []
            data_files = []
            
            # Count HTML cache files
            if os.path.exists(self.html_cache_dir):
                for filename in os.listdir(self.html_cache_dir):
                    if filename.endswith('.html'):
                        filepath = os.path.join(self.html_cache_dir, filename)
                        stat = os.stat(filepath)
                        html_files.append({
                            'filename': filename,
                            'size_kb': round(stat.st_size / 1024, 2),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'valid': self._is_cache_valid(filepath)
                        })
            
            # Count parsed data cache files
            if os.path.exists(self.data_cache_dir):
                for filename in os.listdir(self.data_cache_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.data_cache_dir, filename)
                        stat = os.stat(filepath)
                        data_files.append({
                            'filename': filename,
                            'size_kb': round(stat.st_size / 1024, 2),
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            'valid': self._is_cache_valid(filepath)
                        })
            
            return {
                'cache_dir': self.cache_dir,
                'html_cache_dir': self.html_cache_dir,
                'data_cache_dir': self.data_cache_dir,
                'cache_duration_hours': self.cache_duration.total_seconds() / 3600,
                'html_files': html_files,
                'data_files': data_files,
                'total_html_files': len(html_files),
                'total_data_files': len(data_files),
                'valid_html_files': sum(1 for f in html_files if f['valid']),
                'valid_data_files': sum(1 for f in data_files if f['valid'])
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def clear_cache(self, cache_type: str = 'all') -> Dict:
        """Clear cache files."""
        try:
            cleared = {'html': 0, 'data': 0}
            
            if cache_type in ['all', 'html'] and os.path.exists(self.html_cache_dir):
                for filename in os.listdir(self.html_cache_dir):
                    if filename.endswith('.html'):
                        os.remove(os.path.join(self.html_cache_dir, filename))
                        cleared['html'] += 1
            
            if cache_type in ['all', 'data'] and os.path.exists(self.data_cache_dir):
                for filename in os.listdir(self.data_cache_dir):
                    if filename.endswith('.json'):
                        os.remove(os.path.join(self.data_cache_dir, filename))
                        cleared['data'] += 1
            
            return {
                'success': True,
                'cleared_html_files': cleared['html'],
                'cleared_data_files': cleared['data'],
                'cache_type': cache_type
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Global scraper instance
_scraper = None

def get_scraper() -> FantasyProsScraper:
    """Get or create the global scraper instance."""
    global _scraper
    if _scraper is None:
        _scraper = FantasyProsScraper()
    return _scraper

def get_player_stats(player_names: Union[str, List[str]], year: int, week: Optional[int] = None) -> Dict:
    """
    Main function to get player statistics from FantasyPros.
    
    Args:
        player_names: Player name(s) to look up
        year: NFL season year
        week: NFL week number (None for season stats)
        
    Returns:
        Dictionary containing player statistics
    """
    if isinstance(player_names, str):
        player_names = [player_names]
    
    scraper = get_scraper()
    return scraper.get_player_stats(player_names, year, week)

def get_position_stats(position: str, year: int, week: Optional[int] = None) -> Dict:
    """
    Get all statistics for a specific position from FantasyPros.
    
    Args:
        position: Player position (QB, RB, WR, TE, K)
        year: NFL season year
        week: NFL week number (None for season stats)
        
    Returns:
        Dictionary containing all players for that position
    """
    scraper = get_scraper()
    return scraper.scrape_position_stats(position, year, week)

def get_cache_info() -> Dict:
    """Get information about cached FantasyPros files."""
    scraper = get_scraper()
    return scraper.get_cache_info()

def clear_cache(cache_type: str = 'all') -> Dict:
    """
    Clear FantasyPros cache files.
    
    Args:
        cache_type: Type of cache to clear ('all', 'html', 'data')
        
    Returns:
        Dictionary with results of cache clearing
    """
    scraper = get_scraper()
    return scraper.clear_cache(cache_type)