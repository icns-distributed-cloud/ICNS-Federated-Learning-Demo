<template>
  <el-container style="height: 100vh;padding:1% 3% 0 3%">

    <el-aside style="padding: 20px 30px 0 0">
      <h3>{{this.$t('config')}}</h3>

      <div class="menu">
        {{this.$t('client_num')}}
        <el-input-number
          v-model="clientNum"
          controls-position="right"
          :min="1"
          :max="20"
          size="mini"
          @change="setprocess(0)"
          :disabled="isTraining"
        ></el-input-number>
      </div>

      <div class="menu">
        {{this.$t('dataset')}}
        <el-select v-model="datasetvalue"
                   :placeholder="this.$t('select_a_dataset')"
                   size="mini"
                   @change="loadfeature(); loadtarget()"
                   :disabled="isTraining">
          <el-option
            v-for="item in datasetoptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
            :disabled="item.disabled"
            >
          </el-option>
        </el-select>
      </div>

      <el-divider></el-divider>

      <h3>{{this.$t('post_task')}}</h3>

      <div class="menu">
        {{this.$t('model')}}
        <el-select v-model="modelvalue"
                   :placeholder="this.$t('select_a_model')"
                   size="mini"
                   @change="setprocess(1)"
                   :disabled="isTraining">
          <el-option-group
            v-for="group in modeloptions"
            :key="group.label"
            :label="group.label">
            <el-option
              v-for="item in group.options"
              :key="item.value"
              :label="item.label"
              :value="item.value"
              :disabled="item.disabled">
            </el-option>
          </el-option-group>
        </el-select>
      </div>

      <div class="menu">
        {{this.$t('loss function')}}
        <el-select v-model="lossfuncvalue"
                   :placeholder="this.$t('select_a_loss_function')"
                   size="mini"
                   @change="setprocess(1)"
                   :disabled="isTraining">
            <el-option
              v-for="item in lossfuncoptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
              :disabled="item.disabled">
            </el-option>
        </el-select>
      </div>

      <div class="menu">
        <span>{{this.$t('train_round')}}</span>
        <el-input-number v-model="trainround"
                         :min="1"
                         :max="30"
                         :step="3"
                         size="mini"
                         @focus="setprocess(1)"
                         :disabled="isTraining">
        </el-input-number>
      </div>

      <div v-show="show">
        <el-divider></el-divider>
        <div style="overflow-y: scroll; height:150px;">
          <h3>{{this.$t('select features')}}</h3>
          <div v-for="feature in features" :key="feature">
            <input type="checkbox" :id="feature" :value="feature" v-model="selectedfeatures" :disabled="isTraining">
            <label :for="feature">{{ feature }}</label>
          </div>
        </div>
      </div>

      <div v-show="show">
        <el-divider></el-divider>
        <div style="overflow-y: scroll; height:150px;">
          <h3>{{this.$t('select target')}}</h3>
          <div v-for="target in targets" :key="target">
            <input type="checkbox" :id="target" :value="target" v-model="selectedtargets" :disabled="isTraining">
            <label :for="target">{{ target }}</label>
          </div>
        </div>
      </div>

      <el-divider></el-divider>

      <h3>{{this.$t('train_process')}}</h3>

      <div style="text-align: center;margin-top: 12px">
        <el-button type="success"
                   v-text="btnMsg"
                   @click="startTrain()"
                   size="mini"
                   :disabled="isTraining">
        </el-button>
      </div>
    </el-aside>

    <el-container style="padding: 20px 50px">
      
      <el-main style="border: lightgray dashed 1px;border-radius: 10px;background-color: #f7f8fb"
               v-loading="this.state==='synchronizing...'" element-loading-text="synchronizing...">
        <div style="display: flex;justify-content: flex-start;align-content: flex-start;flex-wrap: wrap">
          
          <Client v-for="(client,index) in clientList" :key="index" :id=index :state="state"
                  :readonly="isTraining" :model="modelvalue" :result="result" :clientnum="clientNum" @ipaddrchange="updateIpAddr"
                  ></Client>
        </div>
      </el-main>

    </el-container>

  </el-container>
</template>

<script>
  import Client from "../components/Client";
  import axios from '../node_modules/axios';
  

  export default {
    name: "home",
    components: {
      Client
    },
    data() {
      
      return {

        activestep: 0,

        //client
        clientNum: 2,
        clientList: [],

        //model
        modeloptions: [{
          label: 'Neural Network',
          options: [
            {
              value: 'CNN',
              label: 'CNN'
            }
          ],
        }, 
        {
          label: 'Linear Models',
          options: [ 
          {
            value: 'Logistic-Regression',
            label: 'Logistic Regression',
            // disabled: true
          }],
        }, 
        ],
        modelvalue: '',

        //loss function
        lossfuncoptions: [
          {
            value: 'categorical_crossentropy',
            label: 'categorical_crossentropy'
          },
          {
            value: 'mean_squared_error',
            label: 'mean_squared_error'
          },
        ],
        lossfuncvalue: '',

        //dataset
        datasetoptions: [
          {
            value: 'mnist',
            label: 'mnist'
          },
          {
            value: 'adult',
            label: 'adult'
          }
        ],
        datasetvalue: '',

        reward: 1000,

        traintime: 30,

        btnMsg: 'Run',

        state: 'free',

        isTraining: false,

        currentpercentage: 0,

        currentstatus: null,

        result: null,

        updatetime: '',

        blockheight: 1023,

        show: false,
        features: [],
        targets: [],
        selectedfeatures: [],
        selectedtargets: [],
        lipaddr: []
      }
    },
    computed: {
    },
    created() {
      this.initClient()
    },
    watch: {
      clientNum: function () {
        this.initClient()
      },
      result: function () {
      }
    },
    methods: {
      add0(m) {
        return m < 10 ? '0' + m : m
      },

      getcurrenttime() {
        var time = new Date();
        var y = time.getFullYear();
        var m = time.getMonth() + 1;
        var d = time.getDate();
        var h = time.getHours();
        var mm = time.getMinutes();
        var s = time.getSeconds();

        return y + '-' + this.add0(m) + '-' + this.add0(d) + ' ' + this.add0(h) + ':' + this.add0(mm) + ':' + this.add0(s)
      },

      initClient() {
        this.clientList = new Array(this.clientNum)
      },
      setprocess(step) {
        this.activestep = step
      },
      startTrain() {
        if (this.datasetvalue === '') {
          this.$message.error('Please select a dataset.');
          return
        }

        if (this.modelvalue === '') {
          this.$message.error('Please select a model.');
          return
        }

        this.btnMsg = 'Running'
        this.state = 'training...'
        this.isTraining = true

        const path = 'http://localhost:5050/api/fl_process'
        var dict_ip = {}
        dict_ip['lipaddr'] = this.lipaddr
        axios.get(path, {
          params: {
            client_num: this.clientNum,
            dataset: this.datasetvalue,
            model: this.modelvalue,
            loss_func: this.lossfuncvalue,
            train_round: this.trainround,
            list_ipaddr: dict_ip
          }
        })
        .then(response => {
          console.log(response.data)
          this.result = response.data
          this.btnMsg = 'Run'
          this.isTraining = false
          this.state = "finish"
          this.$notify({
              title: 'Message',
              message: 'Training Finished!',
              type: 'success'
            })
        })
        .catch(error => {
          console.log(error)
          this.btnMsg = 'Run'
          this.isTraining = false
          this.state = "finish"
          this.$notify({
              title: 'Message',
              message: 'Training Failed!',
              type: 'error'
            })
        })
      },
      
      loadfeature() {
        if (this.datasetvalue === 'adult') {
          this.show = true
          this.selectedfeatures = []
          this.features = ['age', 'workclass', 'education', 'education-num', 'marital-status', 
                          'occupation', 'relationship', 'race', 'sex', 'capital-gain', 'capital-loss', 
                          'hours-per-week', 'native-country']
        }
        else if (this.datasetvalue === 'mnist') {
          this.show = false
          this.selectedfeatures = []
          this.features = []
        }
      },
      loadtarget() {
        if (this.datasetvalue === 'adult') {
          this.show = true
          this.selectedtargets = []
          this.targets = ['class']
        }
        else if (this.datasetvalue === 'mnist') {
          this.show = false
          this.selectedtargets = []
          this.targets = []
        }
      },
      updateIpAddr(ipaddr) {
        this.lipaddr.push(ipaddr)
        console.log(this.lipaddr)
      }
    }
  }
</script>

<style scoped>
  .menu {
    margin-top: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center
  }

</style>
