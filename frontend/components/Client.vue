<template>
  <el-card shadow="always" body-style="padding:20px"
           style="height: 280px;width: 250px;margin: 20px;display: inline-block"
           v-loading="this.state==='training...'" element-loading-text="training..."
           element-loading-spinner="el-icon-loading">

    <div style="display: flex;justify-content:space-around;align-items: center;font-weight: 600">
      <i class="el-icon-monitor"></i>

      <span>{{this.$t('client')}} {{id+1}}</span>

      <span style="color: orange">{{winner}}</span>
    </div>

    <div style="margin-top: 20px;display: flex;justify-content: space-between;align-items: center">
      <span>{{this.$t('state')}}</span>
      {{state}}
    </div>

    <div style="margin-top: 10px;display: flex;justify-content: space-between;align-items: center">
      <span>{{this.$t('Ip Addr')}}</span>
      <input style="width:70%" v-model="ipAddr" @change="inputIpAddr" placeholder="127.0.0.1"> 
    </div>

    <div style="margin-top: 10px;display: flex;justify-content: space-between;align-items: center">
      <span>{{this.$t('accuracy')}}</span>
      {{accu}}
    </div>

    <div style="margin-top: 10px;display: flex;justify-content: space-between;align-items: center">
      <!-- <span>{{this.$t('loss')}}</span> -->
      <span>{{this.$t(losstext)}}</span>
      {{loss}}
    </div>

  </el-card>
</template>

<script>
  export default {
    name: "Client",
    props: {
      id: 0,
      state: '',
      readonly: false,
      model: '',
      result: null,
      clientnum: 0,
    },
    data() {
      return {
        ipAddr: '',
        colors: {2: '#32CD32', 4: '#32CD32', 5: '#32CD32'},
        percentage: 0,
        status: null,
        loss: '--',
        losstext: 'loss',
        accu: '--',
      }
    },
    methods: {
      inputIpAddr: function () {
        this.$emit('ipaddrchange', this.ipAddr);
      },
    },
    created: function () {
      this.$store.commit('add', {
        id: this.id
      });
    },
    destroyed: function () {
      this.$store.commit('remove', {
        id: this.id,
      })
    },
    watch: {
      result: function () {
        this.loss = this.result[this.id.toString()][0]
        this.accu = this.result[this.id.toString()][1]
      },
      state: function (val) {
        // if (val === 'training...') {
          
        // }
        // if (val === 'synchronizing...') {

        // }

      },
      model: function() {
        if (this.model == "CNN") {
          this.losstext = "loss"
        } else {
          this.losstext = "neg_log_loss"
        }
        
      }

    }
  }
</script>

<style scoped>
</style>
