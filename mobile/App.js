import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { View, ActivityIndicator, StatusBar } from 'react-native';
import {
  useFonts,
  Oswald_500Medium,
  Oswald_600SemiBold,
  Oswald_700Bold,
} from '@expo-google-fonts/oswald';
import {
  Inter_400Regular,
  Inter_500Medium,
  Inter_600SemiBold,
} from '@expo-google-fonts/inter';
import {
  JetBrainsMono_400Regular,
  JetBrainsMono_500Medium,
} from '@expo-google-fonts/jetbrains-mono';

import HomeScreen from './src/screens/HomeScreen';
import TeamDetailScreen from './src/screens/TeamDetailScreen';
import NewsScreen from './src/screens/NewsScreen';
import ArticleScreen from './src/screens/ArticleScreen';
import RumorsScreen from './src/screens/RumorsScreen';
import ArchiveScreen from './src/screens/ArchiveScreen';
import { colors, fontFamily } from './src/theme';
import { IcHome, IcNews, IcRumor, IcArchive } from './src/components/icons';

const Tab = createBottomTabNavigator();
const HomeStackNav = createNativeStackNavigator();
const NewsStackNav = createNativeStackNavigator();

const HomeStack = () => (
  <HomeStackNav.Navigator screenOptions={{ headerShown: false }}>
    <HomeStackNav.Screen name="HomeMain" component={HomeScreen} />
    <HomeStackNav.Screen name="TeamDetail" component={TeamDetailScreen} />
    <HomeStackNav.Screen name="Article" component={ArticleScreen} />
  </HomeStackNav.Navigator>
);

const NewsStack = () => (
  <NewsStackNav.Navigator screenOptions={{ headerShown: false }}>
    <NewsStackNav.Screen name="NewsMain" component={NewsScreen} />
    <NewsStackNav.Screen name="Article" component={ArticleScreen} />
  </NewsStackNav.Navigator>
);

const TAB_ICONS = {
  Home: IcHome,
  News: IcNews,
  Rumors: IcRumor,
  Archive: IcArchive,
};

export default function App() {
  const [fontsLoaded] = useFonts({
    Oswald_500Medium,
    Oswald_600SemiBold,
    Oswald_700Bold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    JetBrainsMono_400Regular,
    JetBrainsMono_500Medium,
  });

  if (!fontsLoaded) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.field800, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.gold} />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <StatusBar barStyle="light-content" backgroundColor={colors.field900} />
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerShown: false,
            tabBarStyle: {
              backgroundColor: colors.field900,
              borderTopColor: colors.stroke,
              borderTopWidth: 1,
            },
            tabBarActiveTintColor: colors.gold,
            tabBarInactiveTintColor: colors.muteDim,
            tabBarLabelStyle: {
              fontFamily: fontFamily.body,
              fontSize: 9.5,
              letterSpacing: 0.2,
            },
            tabBarIcon: ({ color }) => {
              const Icon = TAB_ICONS[route.name];
              return <Icon c={color} s={21} />;
            },
          })}
        >
          <Tab.Screen name="Home" component={HomeStack} />
          <Tab.Screen name="News" component={NewsStack} />
          <Tab.Screen name="Rumors" component={RumorsScreen} />
          <Tab.Screen name="Archive" component={ArchiveScreen} />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
