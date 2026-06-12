import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { Text, View, ActivityIndicator } from 'react-native';
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

import HomeScreen from './src/screens/HomeScreen';
import { colors, fontFamily } from './src/theme';

const Tab = createBottomTabNavigator();

const PlaceholderScreen = ({ name }) => (
  <View style={{ flex: 1, backgroundColor: colors.field800, alignItems: 'center', justifyContent: 'center' }}>
    <Text style={{ fontFamily: fontFamily.display, color: colors.muted, fontSize: 16, letterSpacing: 1 }}>
      {name.toUpperCase()} — COMING SOON
    </Text>
  </View>
);

export default function App() {
  const [fontsLoaded] = useFonts({
    Oswald_500Medium,
    Oswald_600SemiBold,
    Oswald_700Bold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
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
      <NavigationContainer>
        <Tab.Navigator
          screenOptions={{
            headerShown: false,
            tabBarStyle: {
              backgroundColor: colors.field900,
              borderTopColor: colors.stroke,
              borderTopWidth: 1,
            },
            tabBarActiveTintColor: colors.gold,
            tabBarInactiveTintColor: colors.muteDim,
            tabBarLabelStyle: {
              fontFamily: fontFamily.mono,
              fontSize: 10,
              letterSpacing: 0.8,
              textTransform: 'uppercase',
            },
          }}
        >
          <Tab.Screen
            name="Home"
            component={HomeScreen}
            options={{ tabBarLabel: 'League' }}
          />
          <Tab.Screen
            name="News"
            children={() => <PlaceholderScreen name="News" />}
            options={{ tabBarLabel: 'News' }}
          />
          <Tab.Screen
            name="Rumors"
            children={() => <PlaceholderScreen name="Rumors" />}
            options={{ tabBarLabel: 'Rumors' }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
}
