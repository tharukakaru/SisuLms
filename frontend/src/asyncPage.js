import {defineAsyncComponent} from 'vue'
import PageLoading from './PageLoading.vue'

export function asyncPage(loader){
  return defineAsyncComponent({loader,loadingComponent:PageLoading,errorComponent:PageLoading,delay:150,timeout:30000})
}
