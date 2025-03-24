import { StyleSheet, Text, View, Pressable,Image } from 'react-native'
import { Method } from '../../assets/types/Method'
import {Link} from 'expo-router'

export const Methods = ({ method }:{method : Method}) => {
  return (
    <Link asChild href={`/upload/${method.name}`}>
      <Pressable style={styles.item}>
          <View style={styles.itemImageContainer}>
            <Image source={method.image} style={styles.itemImage} />
          </View>
          <View style={{ height: 2, backgroundColor: 'black',}} />
          <View style={styles.itemTextContainer}>
            <Text style={styles.itemTitle}>{method.name}</Text>
          </View>
        </Pressable>
      </Link>
  )
}

export default Methods

const styles = StyleSheet.create({
    item: {
        width: '48%',
        backgroundColor: 'white',
        marginVertical: 8,
        borderRadius: 10,
        overflow: 'hidden',
      },
      itemImageContainer: {
        borderRadius: 10,
        width: '100%',
        height: 300,
      },
      itemImage: {
        width: '100%',
        height: '100%',
        resizeMode: 'contain',
      },
      itemTextContainer: {
        padding: 8,
        gap: 4,
      },
      itemTitle: {
        fontSize: 16,
        color: 'black',
        textAlign: 'center',
      },
})